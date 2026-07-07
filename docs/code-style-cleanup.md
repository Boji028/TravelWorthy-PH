# Code style cleanup: Black reformat + lint fixes

**Date:** 2026-07-03

## What changed

First-ever full run of the project's already-configured linting tools
(flake8, Black — both were in requirements.txt and pyproject.toml but
had never been run against the codebase).

### Black auto-reformat

Ran `black .` across the project: 86 files reformatted, 2 unchanged.
Eliminated ~600 pure-style flake8 findings in one pass (trailing
whitespace, blank lines containing whitespace, missing end-of-file
newlines, inconsistent operator spacing, blank-line conventions).
No logic changes — Black only reformats.

### Manual lint fixes (the two real F811 findings)

- `app.py` — removed a redundant `from models.inquiry_notification
  import InquiryNotification` inside the `inject_notifications()`
  context processor; the same import already exists at the top of
  `create_app()` and covers the nested function's scope.
- `routes/main.py` — removed a redundant `import os` inside the
  contact-form email block; `os` is already imported at module level.

### Investigated, no action needed

- `utils.py` "repeated docstrings" in flake8 output — display artifact
  of flake8 re-printing multi-line context per whitespace warning, not
  actual duplication in the file. Black's whitespace cleanup resolved
  the underlying warnings.

## Verification

`pytest --tb=short -q` after Black: 485/485 passed.
(Re-verify again after the two F811 edits.)

## Known remaining lint findings, deliberately deferred

- `C901 create_app is too complex (29)` — app factory has grown large;
  worth extracting init helpers (like the existing `init_oauth()`
  pattern) in a dedicated refactor pass, not as part of a style sweep.
- ~23× `E712` (`assert x == True` style in tests) — style-only,
  functionally identical; low value to churn test files over.
- ~13× `F541` (f-strings without placeholders) — harmless.
- `E402` (imports not at top) in `scripts/` — intentional, these
  scripts do `sys.path.insert()` before importing project modules.
- Unused `as e` in a `utils.py` exception handler — harmless.

## Why

These tools were configured from early in the project but never
actually run, so style drift accumulated invisibly. Running them now
(a) cleans the baseline so future runs only show new findings, and
(b) confirmed via the F811 check that there were no real
shadowed-import bugs hiding in the noise — both duplicates were
benign redundancy.
