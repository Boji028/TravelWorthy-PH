#!/usr/bin/env python
"""Create dummy inquiries backdated to test the auto-delete feature.

TEST DATA ONLY — every row this creates is tagged with the email domain
@dummy-test.invalid (a reserved, guaranteed-fake TLD) and a "TEST DUMMY"
name prefix, so it's unmistakable in the admin Inquiries list and easy to
clean up with delete_dummy_test_inquiries.py afterward.

Creates 4 dummy inquiries covering every branch of the feature:
  1-2. 85 days old, never exported       -> should trigger the reminder
  3.   85 days old, exported yesterday    -> should be EXCLUDED from the
                                             reminder (auto-detect works)
  4.   91 days old                        -> should be DELETED on the
                                             next cleanup run

Run this, then run scripts/run_inquiry_cleanup.py and check the bell
icon + the printed output. See docs/inquiry-auto-delete-after-3-months.md
for the full walkthrough.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from models.inquiry import Inquiry

DUMMY_EMAIL_DOMAIN = "@dummy-test.invalid"


def _make_dummy(label, days_old, exported_days_ago=None):
    today = datetime.now(timezone.utc).date()
    inquiry = Inquiry(
        name=f"TEST DUMMY — {label}",
        email=f"dummy-{label.lower().replace(' ', '-')}{DUMMY_EMAIL_DOMAIN}",
        contact_number="09170000000",
        destination="Dummy Test Destination",
        travel_date_from=today + timedelta(days=30),
        travel_date_to=today + timedelta(days=35),
        status="new",
    )
    db.session.add(inquiry)
    db.session.commit()

    inquiry.created_at = datetime.now(timezone.utc) - timedelta(days=days_old)
    if exported_days_ago is not None:
        inquiry.last_exported_at = datetime.now(timezone.utc) - timedelta(days=exported_days_ago)
    db.session.commit()
    return inquiry


def main():
    app = create_app()
    with app.app_context():
        created = [
            _make_dummy("85 Days Old A", days_old=85),
            _make_dummy("85 Days Old B", days_old=85),
            _make_dummy("85 Days Recently Exported", days_old=85, exported_days_ago=1),
            _make_dummy("91 Days Old - Will Be Deleted", days_old=91),
        ]

        print(f"Created {len(created)} dummy inquiries:")
        for inq in created:
            age = (datetime.now(timezone.utc) - inq.created_at.replace(tzinfo=timezone.utc)).days
            exported = "yes" if inq.last_exported_at else "no"
            print(f"  #{inq.id}  {inq.name}  ({age} days old, exported: {exported})")

        print()
        print("Next: run `python scripts\\run_inquiry_cleanup.py` and check the bell icon.")
        print("When done testing, run `python scripts\\delete_dummy_test_inquiries.py` to clean up.")


if __name__ == "__main__":
    main()
