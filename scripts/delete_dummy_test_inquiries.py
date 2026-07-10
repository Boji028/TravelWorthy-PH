#!/usr/bin/env python
"""Delete every dummy inquiry created by seed_dummy_expiring_inquiries.py.

Matches on the @dummy-test.invalid email domain, so it can never touch a
real inquiry. Deletes via the ORM (not a bulk query) so InquiryNotification
rows tied to these dummy inquiries are cascaded too.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from models.inquiry import Inquiry

DUMMY_EMAIL_DOMAIN = "@dummy-test.invalid"


def main():
    app = create_app()
    with app.app_context():
        dummies = Inquiry.query.filter(Inquiry.email.like(f"%{DUMMY_EMAIL_DOMAIN}")).all()

        if not dummies:
            print("No dummy test inquiries found — nothing to clean up.")
            return

        for inq in dummies:
            db.session.delete(inq)
        db.session.commit()

        print(f"Deleted {len(dummies)} dummy test inquiry(ies).")


if __name__ == "__main__":
    main()
