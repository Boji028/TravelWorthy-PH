# Wire the unused CRLF-stripping guard into email_service._send()

## What was wrong
`email_service.py` defined `_strip_headers()` specifically to "prevent SMTP
header injection", but nothing ever called it. Every outgoing email subject
built from user-controlled data (most notably `inquiry.destination`, set by
anonymous public form submissions with only a `Length(min=2, max=200)`
validator and no CRLF restriction) was interpolated straight into the
`Subject` header via `Message(subject=subject, ...)`. A crafted destination
containing `\r\n` sequences could inject extra header lines into an
outgoing email.

## Fix
`email_service.py::_send()` now passes `_strip_headers(subject)` to
`Message(...)` instead of the raw `subject`. This is a single choke point —
every current and future caller of `_send()` (all subject-building call
sites in the file: `send_inquiry_reply`, `send_admin_new_inquiry`,
`send_inquiry_confirmed`, `send_inquiry_receipt`, and the admin-alert inside
it) is protected without needing to patch each f-string individually.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding S1).
The presence of a purpose-built, never-called sanitizer was the tell —
confirmed by tracing `inquiry.destination` from `forms.py`'s validator
(no CRLF exclusion) through to the five subject-building sites in
`email_service.py`.

## Tests
Added `tests/test_email_service.py::test_send_strips_crlf_from_subject` —
monkeypatches `email_service.mail.send` to capture the outgoing `Message`
and asserts a CRLF-bearing subject reaches it with the line breaks removed.
