# Inquiry submission was slow (~5s) — async email fix

## Cause
`plan_my_trip()` and `inquire_package()` in routes/bookings.py sent two
emails synchronously (customer receipt + admin alert) before returning the
redirect. Each `mail.send()` opens its own SMTP connection to Gmail
(connect + TLS + login + send) — two sequential sends easily adds up to the
~5 seconds observed.

## Fix
- `email_service.py`: added `send_inquiry_emails_async(inquiry_id, base_url)`
  — spawns a daemon thread that re-fetches the inquiry inside its own
  `app.app_context()` and sends both emails there, after the response has
  already gone back to the user.
- `send_inquiry_receipt()` now takes an optional `base_url` param. It used to
  read `request.host_url` directly, which doesn't exist outside a real HTTP
  request — a background thread never has one. `base_url` is captured in the
  route (where `request` is still valid) and passed through.
- `routes/bookings.py`: both routes now call `send_inquiry_emails_async(...)`
  instead of sending emails inline. Removed the now-unused `os` import.

## Verification
Simulated a 2s sleep per `mail.send()` call: response time dropped from a
theoretical ~4s (blocking) to 0.07s, with both emails confirmed to still
fire correctly a few seconds later in the background.

Added `tests/test_bookings.py::TestInquiryEmailIsAsync` to lock this in —
patches `mail.send` to sleep 0.5s and asserts the response returns in under
0.3s, so a future change can't silently reintroduce blocking sends.

## Result
Full suite: 482 passed (was 481).
