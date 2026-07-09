#!/usr/bin/env python
"""Warn admins about, then delete, inquiries older than 3 months.

Run daily via Task Scheduler (see setup_inquiry_cleanup_scheduler.ps1).
Order matters: warn first, so an inquiry gets at least one reminder cycle
before it's actually removed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from logging_service import StructuredLogger


def main():
    app = create_app()
    with app.app_context():
        from inquiry_cleanup_service import notify_admins_of_expiring_inquiries, delete_expired_inquiries

        try:
            at_risk = notify_admins_of_expiring_inquiries()
            if at_risk:
                print(f"Reminder sent: {at_risk} inquiry(ies) at risk of deletion within 7 days.")
            else:
                print("No reminder needed (nothing at risk, or one was already sent recently).")
        except Exception as e:
            print(f"Error sending expiry reminder: {e}")
            StructuredLogger.log_error("inquiry_cleanup", f"Reminder step failed: {str(e)}", {}, "ERROR")
            return 1

        try:
            deleted = delete_expired_inquiries()
            print(f"Deleted {deleted} inquiry(ies) older than 3 months.")
        except Exception as e:
            print(f"Error deleting expired inquiries: {e}")
            StructuredLogger.log_error("inquiry_cleanup", f"Deletion step failed: {str(e)}", {}, "ERROR")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
