# Correct misleading comment in reply_to_inquiry

## What was wrong
`routes/admin.py::reply_to_inquiry()` had comments reading "Send email
FIRST — do not commit until we know it succeeded" and "Only update
database after email is confirmed sent". Neither is true: the return value
of `send_inquiry_reply(...)` is discarded, so nothing here actually checks
whether the email sent, and the DB update proceeds unconditionally.
`docs/fix-silent-inquiry-email-failures.md` documents this as an
intentional, accepted limitation (only `send_inquiry_receipt()`'s return
value is checked) — the behavior was already correct, but the comment
overstated it in a way that could mislead a future maintainer into
thinking failure detection exists here.

## Fix
Reworded both comments to describe what the code actually does and point
at the doc that explains why, instead of claiming a guarantee the code
doesn't provide. No behavior change.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding B3).

## Tests
None needed — comment-only change, no behavior affected.
