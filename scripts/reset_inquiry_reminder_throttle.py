#!/usr/bin/env python
"""Delete existing system-wide 'inquiries expiring soon' notifications so
the reminder throttle resets and you can re-test the full cycle right
away, instead of waiting out the real 48-hour window.

Only touches notifications with inquiry_id IS NULL (the auto-delete
reminders) — never touches per-inquiry notifications like "New inquiry
from X" or a customer's own status updates.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from models.inquiry_notification import InquiryNotification


def main():
    app = create_app()
    with app.app_context():
        system_notifs = InquiryNotification.query.filter(InquiryNotification.inquiry_id.is_(None)).all()

        if not system_notifs:
            print("No system-wide reminder notifications found — throttle is already clear.")
            return

        for n in system_notifs:
            db.session.delete(n)
        db.session.commit()

        print(f"Deleted {len(system_notifs)} system-wide reminder notification(s). Throttle is now clear.")


if __name__ == "__main__":
    main()
