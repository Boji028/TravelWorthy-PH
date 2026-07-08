#!/usr/bin/env python3
"""Seed dummy inquiries for testing the admin dashboard's date filters.

Creates test Inquiry records dated across all of last year (2025) and
across last calendar month (relative to today), so you can verify the
Inquiries admin page's date filtering actually narrows results correctly
(Custom range for a full year, and the built-in "Last month" quick-pick).

Every seeded record is clearly tagged and safe to remove:
  - reference_number starts with "TEST-" (e.g. TEST-00001)
  - email is "seed.test.#####@seed.test"
  - name is prefixed with "[TEST]"
  - special_requests notes "Seed data - safe to delete"

Re-running this script is safe - it picks up numbering after the highest
existing TEST- reference number instead of creating duplicates.

Run scripts/cleanup_test_inquiries.py afterward to remove everything this
script creates.

Usage:
    python scripts/seed_test_inquiries.py
    python scripts/seed_test_inquiries.py --yes
    python scripts/seed_test_inquiries.py --per-month-2025 5 --last-month-count 15
"""
import argparse
import calendar
import os
import random
import re
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # noqa: E402
from models.inquiry import Inquiry  # noqa: E402
from models.package import TourPackage  # noqa: E402

STATUSES = ["new", "contacted", "confirmed", "closed"]
DESTINATIONS = [
    "Palawan, Philippines",
    "Boracay, Philippines",
    "Siargao, Philippines",
    "Batanes, Philippines",
    "Cebu, Philippines",
    "Bohol, Philippines",
    "Japan",
    "South Korea",
    "Singapore",
    "Thailand",
    "Vietnam",
    "Hong Kong",
]
VISA_DESTINATIONS = ["Japan", "South Korea", "Schengen (Europe)", "Australia", "USA"]
FIRST_NAMES = ["Juan", "Maria", "Jose", "Ana", "Pedro", "Rosa", "Carlos", "Liza", "Miguel", "Carmen"]
LAST_NAMES = ["Dela Cruz", "Santos", "Reyes", "Garcia", "Mendoza", "Torres", "Flores", "Ramos"]

SEED_NOTE = "[TEST] Seed data - safe to delete."


def random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def spaced_days(year: int, month: int, count: int) -> list[int]:
    """Return up to `count` distinct days spread across the given month."""
    last_day = calendar.monthrange(year, month)[1]
    count = min(count, last_day)
    return sorted(random.sample(range(1, last_day + 1), count))


def next_seed_seq() -> int:
    """Find the highest existing TEST-##### reference number and return the next one."""
    existing = db.session.query(Inquiry.reference_number).filter(Inquiry.reference_number.like("TEST-%")).all()
    max_seq = 0
    for (ref,) in existing:
        m = re.match(r"TEST-(\d+)$", ref)
        if m:
            max_seq = max(max_seq, int(m.group(1)))
    return max_seq + 1


def make_inquiry(created_at: datetime, seq: int, package_ids: list[int]) -> Inquiry:
    """Build one dummy Inquiry with the given created_at timestamp."""
    kind = random.choices(["trip", "package", "visa"], weights=[0.4, 0.4, 0.2])[0]
    travel_start = created_at.date() + timedelta(days=random.randint(14, 90))
    travel_end = travel_start + timedelta(days=random.randint(2, 10))

    package_id = None
    destination = random.choice(DESTINATIONS)
    special_requests = SEED_NOTE

    if kind == "package" and package_ids:
        package_id = random.choice(package_ids)
    elif kind == "visa":
        destination = random.choice(VISA_DESTINATIONS)
        special_requests = f"[FOR VISA] {SEED_NOTE} Sample visa inquiry message."

    return Inquiry(
        reference_number=f"TEST-{seq:05d}",
        user_id=None,
        package_id=package_id,
        name=f"[TEST] {random_name()}",
        email=f"seed.test.{seq:05d}@seed.test",
        contact_number=f"09{random.randint(100000000, 999999999)}",
        destination=destination,
        travel_date_from=travel_start,
        travel_date_to=travel_end,
        num_adults=random.randint(1, 4),
        num_children=random.randint(0, 2),
        num_infants=0,
        special_requests=special_requests,
        status=random.choice(STATUSES),
        inquiry_type="general",
        created_at=created_at,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    parser.add_argument("--per-month-2025", type=int, default=3, help="records per month across 2025 (default: 3)")
    parser.add_argument("--last-month-count", type=int, default=10, help="records in last calendar month (default: 10)")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        package_ids = [row.id for row in TourPackage.query.with_entities(TourPackage.id).all()]

        today = datetime.now(timezone.utc)
        if today.month == 1:
            last_month_year, last_month_month = today.year - 1, 12
        else:
            last_month_year, last_month_month = today.year, today.month - 1

        total_2025 = args.per_month_2025 * 12
        total_last_month = args.last_month_count
        total = total_2025 + total_last_month

        print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', '?').split('@')[-1]}")
        print(f"\nAbout to create {total} TEST inquiries:")
        print(f"  - {total_2025} spread across all 12 months of 2025 ({args.per_month_2025}/month)")
        print(f"  - {total_last_month} spread across {last_month_year}-{last_month_month:02d} (last month)")
        print(f"  - {len(package_ids)} real package(s) found to link some 'package' type inquiries to")
        print("\nAll records are tagged: reference_number 'TEST-#####', email '@seed.test',")
        print("name prefixed '[TEST]'. Run cleanup_test_inquiries.py afterward to remove them.")

        if not args.yes:
            confirm = input("\nProceed? [y/N] ").strip().lower()
            if confirm != "y":
                print("Aborted.")
                return

        seq = next_seed_seq()
        created = []

        for month in range(1, 13):
            for day in spaced_days(2025, month, args.per_month_2025):
                created_at = datetime(
                    2025, month, day, random.randint(8, 20), random.randint(0, 59), tzinfo=timezone.utc
                )
                created.append(make_inquiry(created_at, seq, package_ids))
                seq += 1

        for day in spaced_days(last_month_year, last_month_month, total_last_month):
            created_at = datetime(
                last_month_year, last_month_month, day, random.randint(8, 20), random.randint(0, 59),
                tzinfo=timezone.utc,
            )
            created.append(make_inquiry(created_at, seq, package_ids))
            seq += 1

        db.session.add_all(created)
        db.session.commit()

        print(f"\nDone - created {len(created)} test inquiries.")
        print("\nGo to Admin > Inquiries and try:")
        print(f"  - Custom range 2025-01-01 to 2025-12-31  -> should show {total_2025}")
        print(f"  - 'Last month' quick-pick ({last_month_year}-{last_month_month:02d})  -> should show {total_last_month}")


if __name__ == "__main__":
    main()
