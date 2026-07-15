# send_inquiry_confirmed: stop eagerly evaluating request.host_url

## Problem
`email_service.py`: `send_inquiry_confirmed()` built its base URL with
`current_app.config.get("SITE_URL", request.host_url)`. The default
argument to `.get()` is evaluated unconditionally — `request.host_url`
runs even when `SITE_URL` is set. Inside a request that's merely
wasteful; outside one it raises "Working outside of request context"
*even though SITE_URL would have been used*. Not reachable today (the
only caller is the `update_inquiry_status` admin route), but the other
senders in this file were moved onto a background thread for exactly
this reason (see inquiry-email-async-fix.md), and this function is the
obvious next candidate — the landmine was worth defusing now.

## Fix
Switched to the guarded form the sibling functions already use:
`current_app.config.get("SITE_URL") or request.host_url`. Behavior in
a request context is identical (except an empty-string SITE_URL now
falls back instead of producing a blank base URL, which is strictly
better). Added a comment so the `.get(key, default)` form doesn't creep
back in.

## Verification
No behavior change on any current path — existing inquiry status
tests pass unchanged.
