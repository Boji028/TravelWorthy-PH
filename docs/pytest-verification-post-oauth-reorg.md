# Full test suite verification: post-OAuth and file reorganization

**Date:** 2026-07-03

## What was verified

Ran the full pytest suite (485 tests) via Claude Code after a batch of
changes: Google OAuth sign-in (added, with Facebook added-then-removed
in the same work session), the register.html password UX redesign,
hardcoded credential fixes across 5 scripts, and a root-level file
reorganization (27 docs moved to docs/, several obsolete scripts
deleted).

**Result: 485/485 passed on the first run.** None of the above changes
broke existing test coverage.

## What was fixed

Two stale doc-comments/docstrings left over from the Facebook
OAuth add-then-remove work — no functional code was affected:

- `models/user.py` — `oauth_provider` field comment still said
  `'google' | 'facebook' | None`; corrected to Google-only
- `oauth.py` — module and `init_oauth()` docstrings still said
  "Google and Facebook"; corrected to Google-only

Re-ran the full suite after these edits — still 485/485.

## Verified clean (no changes needed)

- No leftover Facebook OAuth code anywhere (routes, oauth.py, .env
  files) — remaining "Facebook" references in the codebase are the
  agency's actual Facebook page link in email templates/footer,
  unrelated to OAuth
- Deleted root files (`check_db.py`, `drop_notifications_table.py`,
  `test_comprehensive.py`, `scripts/create_database.py`) have zero
  references anywhere
- Moved scripts and docs have zero references to their old paths
- `tests/conftest.py` builds its own SQLite path independently of
  `DATABASE_URL`, so the PostgreSQL password rotation doesn't affect
  test infrastructure

## Known issue surfaced, not yet fixed

- `pytest.ini` and `pyproject.toml` both define pytest configuration;
  `pytest.ini` wins silently, `pyproject.toml`'s
  `[tool.pytest.ini_options]` block is dead config with a mismatched
  marker set. Not causing failures — flagged for a future cleanup
  pass to remove the dead block and avoid confusion later.
- `test_image.jpg` at project root was intended for deletion in the
  prior file-reorganization pass but the command likely didn't
  complete cleanly (got merged with a subsequent `mkdir` command in
  terminal output). Re-run separately.
