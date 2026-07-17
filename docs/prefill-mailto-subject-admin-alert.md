# Pre-fill Subject on the "Reply to sender" mailto link

**Date:** 2026-07-17

## What changed

`send_contact_admin_alert`'s "Reply to sender" button was a bare
`mailto:{email}` link - no subject, so replying from Gmail always
started with a blank subject line. Now it's
`mailto:{email}?subject={quoted "Re: <original subject>"}`, so Gmail's
compose window opens with the subject already filled in.

Used `urllib.parse.quote` (percent-encoding, `%20` for spaces), not
`quote_plus` (`+` for spaces) - `+` isn't part of the mailto URI spec
(RFC 6068) and isn't reliably decoded back to a space by every mail
client, `%20` is unambiguous everywhere.

## Deliberately not done: pre-filling Cc

Discussed adding a Cc param to the same link. Decided against a
hardcoded default - there's no existing "default contact/agent email"
setting anywhere in the codebase to pull from (unlike inquiries, which
CC whichever agent is assigned to the package), so any address I put
there would be invented, not sourced from real data. Left it out;
happy to add `&cc=<address>` to the link if a specific fixed address is
wanted later.

## What this does NOT change

Still plain text (mailto has no HTML capability), and still completely
disconnected from the app - no admin_response saved, no "Replied"
badge, no audit trail. Those gaps are what the branded admin-panel
reply feature (shipped earlier today) actually solves. This is a small
quality-of-life fix to the old flow, not a replacement for it.

## Tests

Added `test_admin_alert_reply_link_prefills_subject` to
`tests/test_public_pages.py` - submits the public contact form, mocks
the mail send, and asserts the admin alert's mailto link contains the
correctly percent-encoded subject.

Full suite: 587 passed (586 previous + 1 new), 2 pre-existing warnings
unrelated to this change.
