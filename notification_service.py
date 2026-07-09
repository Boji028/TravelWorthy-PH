"""Helpers for creating in-app notifications for logged-in users.

Mirrors the pattern in email_service.py: small, focused functions that
the admin routes call after a state change. Customer-facing notifications
are skipped entirely for guest inquiries (inquiry.user_id is None) since
there's no account to attach them to. Admin notifications always fire
regardless of whether the inquirer is logged in or a guest.
"""
from app import db
from models.inquiry_notification import InquiryNotification


def notify_inquiry_status_change(inquiry, message: str) -> None:
    """Queue an in-app notification for the inquiry's owner, if any.

    Does not commit — callers should commit alongside their own changes
    (e.g. the inquiry.status update) so both happen in one transaction.
    """
    if not inquiry.user_id:
        return
    notif = InquiryNotification(
        user_id=inquiry.user_id,
        inquiry_id=inquiry.id,
        message=message,
    )
    db.session.add(notif)


def notify_inquiry_created(inquiry) -> None:
    """Queue an in-app notification confirming a new inquiry was received.

    Does not commit — callers should commit alongside their own changes.
    Skipped for guest inquiries (no user_id to attach a notification to).
    """
    if not inquiry.user_id:
        return
    notif = InquiryNotification(
        user_id=inquiry.user_id,
        inquiry_id=inquiry.id,
        message=f"We received your inquiry about {inquiry.destination}. We'll be in touch soon!",
    )
    db.session.add(notif)


def notify_admins_new_inquiry(inquiry) -> None:
    """Queue an in-app notification for every admin when a new inquiry comes in.

    Does not commit — caller commits alongside other changes. Fires
    regardless of whether the inquirer is logged in or a guest, mirroring
    the existing send_admin_new_inquiry email alert.
    """
    from models.user import User

    admins = User.query.filter_by(is_admin=True).all()
    for admin in admins:
        notif = InquiryNotification(
            user_id=admin.id,
            inquiry_id=inquiry.id,
            message=f"New inquiry from {inquiry.name} — {inquiry.destination}",
        )
        db.session.add(notif)


def notify_admins_inquiries_expiring(count: int) -> None:
    """Queue a system-wide (inquiry_id=None) in-app notification for every
    admin warning that `count` inquiries are about to be auto-deleted.

    Does not commit — caller commits alongside other changes. Called by
    inquiry_cleanup_service, not tied to any single inquiry, so it's
    skipped entirely by admin.py's per-inquiry cascade delete.
    """
    from models.user import User

    admins = User.query.filter_by(is_admin=True).all()
    plural = "inquiry" if count == 1 else "inquiries"
    message = (
        f"{count} {plural} will be auto-deleted in the next 7 days. "
        "Download them from Inquiries before they're removed."
    )
    for admin in admins:
        notif = InquiryNotification(user_id=admin.id, inquiry_id=None, message=message)
        db.session.add(notif)
