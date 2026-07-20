# Finish the Contact Us messaging removal that was never fully executed

## What was wrong
`docs/remove-contact-messaging-feature.md` (2026-07-19) documents the boss's
decision to remove Contact Us messaging entirely and lists four files under
"Deleted files (won't be removed by extracting the zip — delete manually)".
None of the four were ever actually deleted:

- `models/contact.py`
- `templates/admin/contact_messages.html`
- `scripts/migrate_contact_user.py`
- `tests/test_contact_messages.py`

`tests/test_contact_messages.py` still imported `models.contact.ContactMessage`
and hit `/admin/contact-messages` routes that no longer exist in
`routes/admin.py` (removed correctly there) — 20 of its tests were failing.

## Fix
Deleted all four files. Verified first that nothing else in the repo
references them: `ContactMessage` only remains in
`migrations/versions/b4d8f1a6c3e7_drop_contact_messages_table.py` (expected —
migrations keep historical schema code) and a prose comment in
`tests/test_public_pages.py` (not a code dependency).

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding D2) —
cross-referenced the removal doc's file list against what's actually on
disk.

## Tests
No new tests needed — this only deletes files. Full suite: 558 passed, 0
failed (580 collected at baseline; the 22-test difference is the deleted
`test_contact_messages.py` file, which had a mix of already-failing and
already-passing tests — no test that was passing before is now failing).
