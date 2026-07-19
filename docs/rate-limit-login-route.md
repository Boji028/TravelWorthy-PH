# Rate limit the login route

**Date:** 2026-07-17

## Why

`/auth/login` had no dedicated rate limit — only the global default
(`300 per day, 60 per hour, 10 per minute`, keyed by IP). That allows
up to 10 password guesses a minute against any account before hitting
a wall, and switching IPs resets the count entirely. Every other
credential-adjacent route (`forgot-password`, `resend-verification`)
already gets a tighter, email-keyed limit for exactly this reason.

## What changed

`routes/auth.py::login()` - added:

```python
@limiter.limit(
    "5 per minute; 20 per hour",
    methods=["POST"],
    key_func=lambda: (request.form.get("email", request.remote_addr) or "unknown").lower(),
)
```

Matches the existing `forgot_password`/`resend_verification` pattern
exactly: `methods=["POST"]` so GET page views are never throttled, and
`key_func` keyed by the submitted email (falling back to IP, then
`"unknown"`) so the limit tracks a specific account rather than a
specific visitor — someone can't dodge it by switching IPs, and a flood
against one account doesn't lock out anyone else.

Used the already-fixed version of that `key_func` lambda (the `or
"unknown"` guard) - an earlier session found and fixed a crash in this
exact lambda on `forgot_password` when both `email` and `remote_addr`
were empty. Copied the fixed version, not the original bug.

5/minute is slightly more forgiving than forgot-password's 5/hour,
since a genuine visitor mistyping a password is far more common than
someone requesting a password reset multiple times, and login is much
higher-traffic. 20/hour still catches sustained slow-drip attempts a
1-minute-window alone wouldn't.

## Tests

Added to `TestUserLogin` in `tests/test_auth.py`:
- `test_login_page_views_are_not_rate_limited`
- `test_repeated_failed_logins_get_rate_limited`
- `test_login_rate_limit_is_keyed_by_email_not_shared_globally`
- `test_login_does_not_crash_with_no_email_and_no_remote_addr`

Also verified `admin_client`/`authenticated_client` test fixtures
inject the Flask-Login session directly rather than POSTing to
`/auth/login`, so this change has zero effect on the hundreds of other
tests that use those fixtures.

Full suite: 591 passed (587 previous + 4 new), 2 pre-existing warnings
unrelated to this change.
