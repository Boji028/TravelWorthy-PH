# Scope forgot-password / resend-verification rate limits to POST only

## Problem
`routes/auth.py`: the `5 per hour` limits on `forgot_password` and
`resend_verification` applied to the whole route — GET page views
included. On a GET the form is empty, so the key_func's
`request.form.get("email", request.remote_addr)` fell through to the
IP address: five page loads from one IP in an hour and the sixth
visitor behind that IP got the 429 page without ever submitting
anything. Shared IPs (offices, campuses, CGNAT) make this a real
lockout, not a corner case — and it directly contradicts the intent
documented in scope-rate-limits-to-auth-and-inquiry-routes.md (throttle
email-sending abuse, i.e. POSTs). The contact and inquiry routes
already used `methods=["POST"]`; these two were the odd ones out.

## Fix
Added `methods=["POST"]` to both `@limiter.limit(...)` decorators,
matching the pattern in `routes/main.py` (`contact`) and
`routes/bookings.py` (`plan_my_trip`, `inquire_package`). The POST
behavior — 5/hour keyed by submitted email — is unchanged.

## Tests
- `test_forgot_password_page_views_are_not_rate_limited` /
  `test_resend_verification_page_views_are_not_rate_limited`: 7 GETs
  in a row all return 200. Verified the forgot-password one fails
  (429 on the 6th GET) with the fix stashed, passes with it applied.
- `test_resend_verification_does_not_crash_with_no_email_and_no_remote_addr`
  switched from GET to POST — with the limiter scoped to POST, a GET
  no longer runs the key_func at all, so the old form of the test
  would have stopped exercising the None-guard it was written for.
  (The forgot-password twin already used POST.)
