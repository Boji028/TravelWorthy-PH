# Fix silent inquiry email failures — the last "flagged, not fixed" item

## The actual inconsistency
Forgot-password tells the user outright: "Failed to send reset email."
Inquiry submission (Plan My Trip, package inquiries) sends its
confirmation email asynchronously in a background thread — by design,
to avoid a slow SMTP round trip blocking the response — which means by
the time a send failure would happen, the customer's page has already
loaded. There was never a way to tell them synchronously. What was
missing wasn't a message on that page; it was any signal *anywhere*
that it had failed, beyond a line in the server log nobody was
watching.

## What "fixed" means here, given the async constraint
Didn't make inquiry email sending synchronous — that would undo a
deliberate prior fix (see the email-thread work earlier this project)
for no good reason. Instead: track the failure on the `Inquiry` record
itself, and surface it in the two places where it's actually useful —
which turned out to both be *better* than a same-page error message,
not just a workaround:

- **The public tracking page** — the customer is given this link
  regardless of outcome, and by the time they check it (even
  immediately after submitting), the async send has had time to
  complete either way, so the page can accurately say whether a
  confirmation email actually went out.
- **The admin inquiries list** — a small warning icon next to the
  customer's email, so staff can notice and follow up manually instead
  of the failure being invisible to everyone but the log file.

## The real bug this surfaced: exceptions never reached the worker at all
First attempt wrapped `send_inquiry_receipt()` in a try/except inside
the async worker — reasonable-looking, but it never actually caught
anything, confirmed by the first test run: `confirmation_email_failed`
stayed `False` even when the simulated send raised. Root cause:
`email_service.py`'s low-level `_send()` helper — used by every email
in this file — already wraps `mail.send()` in its own try/except and
just logs the error, **never re-raising**. That's true of all ~10 email
functions in this file, not just inquiries: every failure in this
codebase has always been silent at the lowest level, logged and
nothing else.

Fixed properly rather than adding a second layer of exception handling
that would've had the same problem: `_send()` now returns `bool`
(success/failure) instead of implicitly `None`, and `send_inquiry_receipt()`
propagates that return value instead of discarding it. This is
additive-only for the other ~8 callers of `_send()` in this file — none
of them check its return value today, so a bare statement ignoring a
`bool` instead of ignoring `None` changes nothing for them. Only
`send_inquiry_receipt()`'s signature changed, from `-> None` to `-> bool`.

The async worker's try/except around the call stays too, as
defense-in-depth — `send_inquiry_receipt()` does template/URL work
*before* it ever reaches `_send()`, and that part genuinely could raise
for an unrelated reason. The primary signal is now the return value;
the try/except is a backstop, not the main mechanism.

## Second thing this surfaced: one failure was silently skipping the other email entirely
The original code had `send_inquiry_receipt()` and `send_admin_new_inquiry()`
sharing one try block. If the customer receipt raised, `send_admin_new_inquiry()`
never ran at all — meaning a customer email hiccup meant the admin
never even heard about the new inquiry either, compounding the
original problem instead of just leaving it half-silent. Split into two
independent try/excepts so each send is attempted regardless of what
the other one did. Verified with a test that fails the first send,
succeeds the second, and asserts both were actually attempted (`call_count == 2`).

## Changes
- `models/inquiry.py`: new `confirmation_email_failed` column (nullable
  boolean, `server_default="false"` — trivial migration, no backfill
  concerns like the earlier `session_token` column had).
- `email_service.py`: `_send()` returns `bool`; `send_inquiry_receipt()`
  propagates it; `send_inquiry_emails_async()`'s worker checks it and
  sets the flag, and the two sends are now independent.
- `templates/admin/inquiries.html`: warning icon next to the customer's
  email when the flag is set.
- `templates/main/inquiry_status.html`: a notice box on the tracking
  page when the flag is set, telling the customer their inquiry was
  received even though no confirmation email arrived.

## Migration needed
```
flask db migrate -m "add confirmation_email_failed to inquiries"
flask db upgrade
```

## Verification
- Full suite: 561/561 passing (555 baseline + 6 new tests: two proving
  the failure-tracking + independent-sends fix via the real threaded
  worker (`@pytest.mark.real_async_email`, not the autouse stub), two
  for the tracking page notice, two for the admin badge).
- The core bug — exceptions never reaching the worker — was caught by
  the first version of the test actually failing, not assumed fixed
  from reading the code.
