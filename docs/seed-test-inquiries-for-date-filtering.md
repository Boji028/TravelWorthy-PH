# Seed test inquiries for date filtering QA

## Problem
No easy way to verify the Inquiries admin page's date filters (Custom
range, "Last month" quick-pick) actually narrow results correctly,
since there was no data outside the current month.

## What was added
Two new scripts, both using the existing `app.py` / `db` app-context
pattern (same as `scripts/check_data_integrity.py`):

### `scripts/seed_test_inquiries.py`
Creates dummy `Inquiry` rows spread across:
- All 12 months of 2025 (default 3/month = 36 records) — for testing
  "last year" via the Custom range picker (2025-01-01 to 2025-12-31).
- Last calendar month, computed relative to today (default 10 records)
  — for testing the built-in "Last month" quick-pick.

Every seeded record is clearly tagged so it can never be mistaken for
a real customer inquiry:
- `reference_number` starts with `TEST-` (e.g. `TEST-00001`)
- `email` is `seed.test.#####@seed.test`
- `name` is prefixed `[TEST]`
- `special_requests` notes "Seed data - safe to delete"

Records vary status (new/contacted/confirmed/closed) and type
(trip/package/visa, using the same `[FOR VISA]` prefix convention the
app already uses) so the status pills and type filter can be tested
too, not just date.

Re-running the script is safe — it looks up the highest existing
`TEST-#####` reference number and continues from there instead of
colliding on the unique constraint.

Usage:
```
python scripts/seed_test_inquiries.py
python scripts/seed_test_inquiries.py --yes
python scripts/seed_test_inquiries.py --per-month-2025 5 --last-month-count 15
```

### `scripts/cleanup_test_inquiries.py`
Deletes every `Inquiry` where `reference_number LIKE 'TEST-%'`. Deletes
through `db.session.delete()` (not a bulk query) so the
`cascade="all, delete-orphan"` on `Inquiry.notifications`
(`models/inquiry_notification.py`) is respected if any seeded inquiry
were ever linked to a real account. Safe to re-run; no-ops if nothing
matches.

Usage:
```
python scripts/cleanup_test_inquiries.py
python scripts/cleanup_test_inquiries.py --yes
```

## Verification
Ran both scripts against a throwaway SQLite copy of the schema:
- Seeded 46 records (36 in 2025, 10 in June 2026) — direct DB query
  confirmed exactly 36 rows in the 2025-01-01..2026-01-01 range and
  exactly 10 in the June 2026 range.
- Re-ran with different counts — no unique-constraint collisions,
  numbering continued from `TEST-00046` onward.
- Cleanup deleted all 60 accumulated test rows, confirmed 0 remaining.

No migration needed — this only inserts/deletes rows in the existing
`inquiries` table.
