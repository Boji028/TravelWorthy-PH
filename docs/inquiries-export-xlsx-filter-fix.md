# Inquiries export: CSV to filtered Excel

## What happened
The "Export CSV" button on the Inquiries admin page only respected the
status filter. If an admin filtered the on-screen list by search term,
inquiry type (package/visa/trip), or date range and then exported, the
download silently ignored those filters and dumped every inquiry instead.

## Decision
Converted the export to a real `.xlsx` file (bold header row, frozen top
row, sized columns, native Excel date formatting) instead of CSV, since
that was the actual ask. Added `openpyxl` as a new dependency for this.

Extracted the filter logic that `inquiries()` already had into two shared
helpers so the list view and the export can never drift apart again:
- `_get_inquiry_filter_params()` — reads/normalizes the query params.
- `_apply_inquiry_filters()` — applies type/search/date-range filtering.

## Changes
- `routes/admin.py`
  - Added `_get_inquiry_filter_params()` and `_apply_inquiry_filters()`.
  - `inquiries()` now calls the shared helpers instead of an inline closure.
  - `export_inquiries()` now applies the full filter set (status, type,
    search, month/year/date range, sort) and writes an `.xlsx` workbook
    via openpyxl instead of CSV.
  - Removed the now-unused `csv` import.
- `templates/admin/inquiries.html` — Export link now passes through every
  active filter param, not just `status`; label/icon updated to
  "Export Excel".
- `requirements.txt` — added `openpyxl==3.1.5`.
- `tests/test_admin_lists.py` — `TestExportInquiries` rewritten to read
  the `.xlsx` response via openpyxl instead of scanning raw CSV bytes;
  added `test_search_filter_applied`, `test_type_filter_applied`, and
  `test_date_range_filter_applied` regression tests.

## Result
Full suite: 485 passed (482 existing + 3 new).
