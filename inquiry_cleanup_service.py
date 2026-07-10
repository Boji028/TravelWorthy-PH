"""Auto-delete old inquiries and warn admins before it happens.

Two independent steps, both called by scripts/run_inquiry_cleanup.py:

1. notify_admins_of_expiring_inquiries() - inquiries within 7 days of the
   3-month cutoff that haven't been exported recently get a system-wide
   admin notification ("N inquiries will be auto-deleted..."), throttled
   to roughly every 2 days so admins get warned several times a week
   without being spammed daily.
2. delete_expired_inquiries() - inquiries past the full 3-month cutoff are
   deleted via the ORM (not a bulk query.delete()), so the existing
   cascade="all, delete-orphan" relationship on InquiryNotification
   actually fires instead of leaving orphaned notification rows behind.

Every datetime comparison here is done as a SQL filter (Inquiry.created_at
<= cutoff, etc.), never by fetching a value back and comparing it in
Python. This matters because db.DateTime columns are TIMESTAMP WITHOUT
TIME ZONE: if the Postgres session's `timezone` setting isn't UTC, an
aware datetime.now(timezone.utc) gets silently converted to that session
timezone before the naive value is stored. A SQL filter is still correct
because the same conversion is applied consistently to both the stored
column and the filter's bind parameter. A Python-side comparison against
a value fetched back from the DB is NOT safe, because there's no way to
tell from the naive datetime alone whether it's UTC or session-local
content — see the throttle check below, which used to do exactly that
and produced a negative "hours ago" on a non-UTC session.
"""
from datetime import datetime, timezone, timedelta
from app import db
from models.inquiry import Inquiry
from models.inquiry_notification import InquiryNotification
from logging_service import StructuredLogger

RETENTION_DAYS = 90  # ~3 months
WARNING_WINDOW_DAYS = 7  # start warning this many days before deletion
REEXPORT_SUPPRESS_DAYS = 7  # skip inquiries the admin already downloaded within this window
REMINDER_THROTTLE_HOURS = 48  # don't re-notify more often than this (~3-4x/week)


def notify_admins_of_expiring_inquiries() -> int:
    """Queue a reminder notification if there are un-downloaded inquiries
    about to be auto-deleted, unless one was already sent recently.

    Returns the count of at-risk inquiries found (0 if none, or if a
    reminder was skipped due to the throttle).
    """
    from notification_service import notify_admins_inquiries_expiring

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RETENTION_DAYS)
    warning_start = now - timedelta(days=RETENTION_DAYS - WARNING_WINDOW_DAYS)
    reexport_cutoff = now - timedelta(days=REEXPORT_SUPPRESS_DAYS)
    throttle_cutoff = now - timedelta(hours=REMINDER_THROTTLE_HOURS)

    at_risk = Inquiry.query.filter(
        Inquiry.created_at <= warning_start,
        Inquiry.created_at > cutoff,
        db.or_(Inquiry.last_exported_at.is_(None), Inquiry.last_exported_at < reexport_cutoff),
    ).count()

    if at_risk == 0:
        return 0

    throttled = db.session.query(
        InquiryNotification.query.filter(
            InquiryNotification.inquiry_id.is_(None),
            InquiryNotification.created_at >= throttle_cutoff,
        ).exists()
    ).scalar()
    if throttled:
        return 0

    notify_admins_inquiries_expiring(at_risk)
    db.session.commit()
    StructuredLogger.log_admin_action("inquiry_expiry_reminder_sent", "inquiry", None, {"at_risk_count": at_risk})
    return at_risk


def delete_expired_inquiries() -> int:
    """Delete every inquiry older than RETENTION_DAYS, any status.

    Deletes one at a time via db.session.delete() (not a bulk
    query.delete()) so InquiryNotification's cascade="all, delete-orphan"
    actually removes that inquiry's notifications too, instead of leaving
    them orphaned or hitting a foreign key error.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    expired = Inquiry.query.filter(Inquiry.created_at <= cutoff).all()

    count = len(expired)
    for inquiry in expired:
        db.session.delete(inquiry)

    if count:
        db.session.commit()
        StructuredLogger.log_admin_action("inquiries_auto_deleted", "inquiry", None, {"deleted_count": count})

    return count
