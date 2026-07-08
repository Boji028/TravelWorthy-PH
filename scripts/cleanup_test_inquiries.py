#!/usr/bin/env python3
"""Remove all seeded test inquiries created by seed_test_inquiries.py.

Deletes every Inquiry row whose reference_number starts with "TEST-".
Deletes through the ORM (db.session.delete) rather than a bulk query so
the cascade="all, delete-orphan" on Inquiry.notifications is respected -
matters if any seeded inquiry ever got linked to a user account.

Safe to run repeatedly; does nothing if no test data exists.

Usage:
    python scripts/cleanup_test_inquiries.py
    python scripts/cleanup_test_inquiries.py --yes
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # noqa: E402
from models.inquiry import Inquiry  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        matches = Inquiry.query.filter(Inquiry.reference_number.like("TEST-%")).all()
        if not matches:
            print("No test inquiries found (reference_number LIKE 'TEST-%'). Nothing to do.")
            return

        print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', '?').split('@')[-1]}")
        print(f"Found {len(matches)} test inquiries to delete.")

        if not args.yes:
            confirm = input("Delete them all? [y/N] ").strip().lower()
            if confirm != "y":
                print("Aborted.")
                return

        for inq in matches:
            db.session.delete(inq)
        db.session.commit()
        print(f"Deleted {len(matches)} test inquiries.")


if __name__ == "__main__":
    main()
