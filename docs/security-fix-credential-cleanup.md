# Security fix: hardcoded DB credentials + root-level file cleanup

**Date:** 2026-07-02/03

## What changed

### Security fix (primary)

Found hardcoded PostgreSQL credentials (`password="Enzo123"`) in five
files, all tracked by git and pushed to `Boji028/TravelWorthy-PH`:

- `clean_accounts.py` (root)
- `debug_users.py` (root)
- `reset_admin_password.py` (root)
- `create_pg_db.py` (root)
- `scripts/create_database.py`

All five rewritten to read the connection from `DATABASE_URL` in
`.env` instead (matching the pattern `check_db.py` /
`scripts/test_postgres_connection.py` already used correctly).
`reset_admin_password.py` now prompts for the new password
interactively (hidden input) instead of hardcoding
`"Admin12345"` in plaintext. `debug_users.py` no longer has
hardcoded test account emails/passwords baked in, and no longer
prints password hashes to the console.

**Action taken:** local PostgreSQL password rotated (old password is
permanently in git history now, treated as compromised).
`DATABASE_URL` in `.env` updated to match.

**Not yet done:** git history itself still contains the old password
in every commit that touched these files. If `Boji028/TravelWorthy-PH`
is a public repo, scrubbing history with `git filter-repo` (or GitHub's
secret-removal tooling) is worth doing as a follow-up — not done here
since it rewrites commit hashes and needs a deliberate, separate pass.

### File reorganization

Root of `fixed/` had 23 loose `.py` files mixing real application
modules with one-off diagnostic/maintenance scripts. Cleaned up:

**Deleted (obsolete, superseded, or unsafe to keep):**
- `check_db.py` — duplicate of `scripts/test_postgres_connection.py`
- `drop_notifications_table.py` — one-off migration already applied;
  `inquiry_notifications` is now a permanent table via
  `InquiryNotification` model, this script was a live footgun
- `scripts/create_database.py` — hardcoded credentials, and targeted
  the wrong database name (`travel_agency` instead of the real
  `travel_agency_db`)
- `test_comprehensive.py` — a hand-rolled `TestRunner` class
  predating the real pytest suite. Not collected by pytest
  (`testpaths = tests` in `pytest.ini`/`pyproject.toml`), so it
  wasn't running automatically. Coverage (environment, database,
  forms, auth, packages, inquiries, contact, error handling) is a
  strict subset of what the 485 real pytest tests already cover.

**Moved `root/` → `scripts/` (rewritten to remove hardcoded creds):**
- `clean_accounts.py`
- `debug_users.py`
- `reset_admin_password.py`
- `create_pg_db.py`

**Moved and renamed:**
- `test_email.py` → `scripts/manual_test_email.py` (renamed so it's
  never mistaken for a real pytest test file)

## Why

The credential exposure was the priority — hardcoded secrets in a
version-controlled repo are a real risk regardless of repo visibility.
The file reorganization was a related cleanup: root-level clutter
made it hard to tell application code apart from one-off scripts, and
in the process of moving things, several already-obsolete or
duplicate/conflicting scripts turned up (`create_database.py` vs
`create_pg_db.py` targeting different DB names being the clearest
example).

## Follow-up

- Consider `git filter-repo` to scrub the old password from git
  history if the repo is public
- No other loose root-level scripts identified as needing similar
  treatment in this pass — `cli.py`, `oauth.py`, `backup_*.py`,
  `email_service.py`, etc. remain at root since they're real
  application modules imported elsewhere, not one-off scripts
