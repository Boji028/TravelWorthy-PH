# Fix missing openpyxl dependency

## Problem
Full test suite run showed 8 failures, all in TestExportInquiries
(tests/test_admin_lists.py) — every hit to the inquiry export endpoint
raised ModuleNotFoundError on a clean install.

## Root cause
routes/admin.py imports openpyxl directly (Workbook, styles, utils) to
build the filter-aware xlsx inquiry export, but openpyxl was never added
to requirements.txt. It only worked locally because it was already
installed in that venv from when the export feature was built — a fresh
install from requirements.txt (new machine, CI, redeploy) breaks the
export feature with a 500.

## Files changed
- requirements.txt — added openpyxl==3.1.5

## Verification
- All 9 tests in TestExportInquiries pass after adding the dependency
  and reinstalling.
- Full suite: 485 passed, 0 failed.