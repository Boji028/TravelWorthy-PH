# Delete orphaned models/admin.py duplicate

## What was wrong
`models/admin.py` (2,325 lines) was a stray, unimported near-duplicate of
`routes/admin.py` (2,209 lines) — an older snapshot from before the Contact
Us messaging feature was removed. It still contained the five contact-
message routes (`contact_messages`, `mark_message_read`,
`reply_to_contact_message`, `delete_contact_messages_bulk`,
`delete_contact_message`) and the `ContactMessage` import that were
correctly removed from the real `routes/admin.py`.

Git history shows this file's only commit is `ccc94bd` — the same commit
that accidentally regressed `notification_service.py`
(`docs/restore-notification-service-regression.md`) — consistent with it
being an accidental stray write from that commit rather than an
intentional file.

## Fix
Deleted `models/admin.py` outright. Confirmed zero references anywhere in
the repo before deleting: `grep -rn "models\.admin"` across all `.py` files
returned nothing, and `models/__init__.py` doesn't import it.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding D1).

## Tests
No test changes needed — the file was never imported or exercised by any
test. Full suite unaffected.
