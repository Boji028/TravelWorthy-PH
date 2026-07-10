#!/usr/bin/env python
"""Print exactly why notify_admins_of_expiring_inquiries() did or didn't
fire, without changing anything. Read-only — safe to run any time.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from models.inquiry import Inquiry
from models.inquiry_notification import InquiryNotification
from inquiry_cleanup_service import RETENTION_DAYS, WARNING_WINDOW_DAYS, REEXPORT_SUPPRESS_DAYS, REMINDER_THROTTLE_HOURS


def main():
    app = create_app()
    with app.app_context():
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=RETENTION_DAYS)
        warning_start = now - timedelta(days=RETENTION_DAYS - WARNING_WINDOW_DAYS)
        reexport_cutoff = now - timedelta(days=REEXPORT_SUPPRESS_DAYS)
        throttle_cutoff = now - timedelta(hours=REMINDER_THROTTLE_HOURS)

        print(f"Server UTC now:      {now}")
        print(f"Delete cutoff:       {cutoff}  (created_at <= this gets deleted)")
        print(f"Warning window start:{warning_start}  (created_at <= this AND > cutoff = at risk)")
        print(f"Re-export suppress:  {reexport_cutoff}  (last_exported_at older than this doesn't suppress)")

        if db.engine.dialect.name == "postgresql":
            session_tz = db.session.execute(db.text("SHOW timezone")).scalar()
            print(f"Postgres session timezone: {session_tz!r}", end="")
            if session_tz and session_tz.upper() not in ("UTC", "ETC/UTC"):
                print("  <-- NOT UTC. This is why raw timestamps below look shifted.")
            else:
                print()
        print()

        print("=== Dummy inquiries (@dummy-test.invalid) ===")
        dummies = Inquiry.query.filter(Inquiry.email.like("%@dummy-test.invalid")).order_by(Inquiry.id).all()
        if not dummies:
            print("  None found. Did the seed script run against THIS database?")
            print("  Check DATABASE_URL matches what run_inquiry_cleanup.py used.")
        for inq in dummies:
            # All of these run as SQL filters (not a Python-side comparison
            # against a fetched value), so they're correct regardless of
            # what timezone Postgres actually stored the raw value in.
            in_warning_window = (
                Inquiry.query.filter(Inquiry.id == inq.id, Inquiry.created_at <= warning_start, Inquiry.created_at > cutoff).count()
                > 0
            )
            past_cutoff = Inquiry.query.filter(Inquiry.id == inq.id, Inquiry.created_at <= cutoff).count() > 0
            recently_exported = (
                Inquiry.query.filter(Inquiry.id == inq.id, Inquiry.last_exported_at >= reexport_cutoff).count() > 0
            )
            would_count = in_warning_window and not recently_exported
            print(f"  #{inq.id} {inq.name!r}")
            print(f"      created_at (raw from DB): {inq.created_at}")
            print(f"      last_exported_at (raw):   {inq.last_exported_at}")
            print(f"      past deletion cutoff: {past_cutoff}  |  in warning window: {in_warning_window}  |  recently exported: {recently_exported}")
            print(f"      >>> counts toward 'at risk' right now: {would_count}")
        print()

        print("=== Throttle state (SQL-level check, matches the actual code) ===")
        throttled = db.session.query(
            InquiryNotification.query.filter(
                InquiryNotification.inquiry_id.is_(None),
                InquiryNotification.created_at >= throttle_cutoff,
            ).exists()
        ).scalar()
        last_reminder = (
            InquiryNotification.query.filter(InquiryNotification.inquiry_id.is_(None))
            .order_by(InquiryNotification.created_at.desc())
            .first()
        )
        if last_reminder:
            print(f"  Most recent system-wide reminder: {last_reminder.created_at}  (raw from DB)")
            print(f"  Message: {last_reminder.message!r}")
        else:
            print("  No system-wide reminder notification exists yet.")
        print(f"  >>> currently blocking new reminders: {throttled}")


if __name__ == "__main__":
    main()
