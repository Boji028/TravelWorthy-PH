# ProxyFix, review-form gate, and password-reset session invalidation

## Context
Three items from the end-to-end journey pass: one to fix outright
(ProxyFix — a second, independent way to hit Google's
`redirect_uri_mismatch`, beyond just remembering to update the console
setting), one confirmed as a real UX gap and fixed (review form
rendering for ineligible users), and one accepted as worth doing
despite being non-blocking (password reset not invalidating other
sessions — OWASP-recognized gap, not just theoretical hardening).

## 1. ProxyFix
`app.py`: wrapped `app.wsgi_app` with `werkzeug.middleware.proxy_fix.ProxyFix`
(`x_for=1, x_proto=1, x_host=1, x_prefix=1` — trusting exactly one hop,
matching Render's architecture: client → Render's edge proxy → this
container). Without it, the app only ever sees plain HTTP internally
even when the visitor is on HTTPS, since Render terminates TLS at the
proxy. Every `url_for(..., _external=True)` call in this codebase
(Google OAuth's redirect_uri, the password reset link, the email
verification link) would silently build an `http://` URL as a result —
which is exactly what causes Google's `redirect_uri_mismatch` even when
the console's configured redirect URI is character-for-character
correct.

Also set `PREFERRED_URL_SCHEME = "https"` when `FLASK_FORCE_HTTPS` is
on, as a defensive default for any future URL built outside a request
context (none currently exist — all three `_external=True` call sites
run inside a real request — but cheap to set regardless).

**Verified this was a real, reproducible bug**, not a theoretical
config nitpick: wrote a test that sends a password-reset request with
`X-Forwarded-Proto: https`, intercepts the outgoing email, and checks
the embedded reset link's scheme. Reverted `ProxyFix` locally, watched
the link come back as `http://` exactly as predicted, restored the fix,
confirmed `https://`.

## 2. Review form now gated on eligibility, not just submission
`routes/packages.py`: `package_detail()` (the GET route rendering the
page) didn't know anything about the confirmed-booking requirement —
only `submit_review()` (the POST handler) enforced it, meaning any
logged-in user saw the full review form and only found out they
weren't eligible after writing a review and hitting submit.

`package_detail()` now computes the same eligibility check and passes
it as `can_review`. Extracted the query itself into a shared
`_can_review_package(user_id, package_id)` helper used by both routes,
rather than duplicating the exact query in both places — that
duplication is exactly how this bug happened in the first place: one
copy of the rule got enforced, the other was simply never written.

`templates/packages/detail.html`: added a new `{% elif not can_review %}`
branch between the "already reviewed" and "write a review" branches,
showing an explanatory message instead of the form.

## 3. Password reset invalidates other active sessions
The real gap: an already-open session (an attacker's, if the reset was
prompted by suspecting compromise) kept working right through a
password reset, since Flask-Login's default session mechanism only
ever checks "does this user ID exist," never "was this specific session
issued before or after the last password change."

Implemented Flask-Login's documented pattern for this — an
"alternative token" embedded in the session identifier:

- `models/user.py`: new nullable `session_token` column. `get_id()`
  (what Flask-Login calls to decide what goes in the session cookie)
  now returns `"<id>:<token>"` instead of a bare ID, lazily generating
  a token on first use if the account doesn't have one yet — so no
  data-backfill migration is needed, every user gets one the next time
  they log in regardless. New `rotate_session_token()` method replaces
  it with a fresh value.
- `load_user()` (the `@login_manager.user_loader` callback) now parses
  that composite ID: if the embedded token doesn't match the user's
  *current* `session_token`, returns `None` — Flask-Login treats that
  as "not logged in." A bare numeric ID with no `:` (a session cookie
  issued before this feature existed) is still honored once, rather
  than force-logging out every already-signed-in user the moment this
  deploys — those upgrade to the token-aware format the next time that
  user actually logs in again.
- `password_reset_service.py`: `reset_password()` now calls
  `user.rotate_session_token()` alongside setting the new password
  hash — this is the actual fix.
- `routes/auth.py`: `profile()` (the logged-in "change password" flow)
  does the same, for the identical threat model — but since
  `current_user` *is* the session making the change, rotating the
  token would log that session out too unless it's immediately
  re-logged-in with the new token. Added `login_user(...)` right after
  the rotation to keep the current session valid while any *other*
  session for the account gets invalidated.

**Bug caught by testing this, not shipped blind:** the first attempt
passed `current_user` (Flask-Login's `LocalProxy`) directly into
`login_user()`, which triggered a `RecursionError` inside
`flask_login`'s internals. Fixed by unwrapping it with
`current_user._get_current_object()` first — `login_user()` needs the
real `User` object, not the proxy.

**Second bug caught while writing the cross-session test:** an
integration test simulating two separate logged-in "devices" for the
same user initially showed the reset *not* invalidating the first
device's session — looked like the whole fix didn't work. Root cause:
Flask-Login caches the loaded user into `flask.g`, which is scoped to
the *app context*, not the request. This project's `app` test fixture
deliberately keeps one app context open for the whole test (to avoid a
`DetachedInstanceError` elsewhere), so the first "device"'s cached user
leaked into the authentication check for the second, genuinely separate
client/cookie jar. Not a real application bug — confirmed by testing
the exact same scenario with `g.pop("_login_user", None)` between each
simulated device, which produced the correct result. In an actual
deployment this doesn't happen; every incoming request gets its own
fresh context naturally. Documented this directly in the test's
docstring so it isn't mistaken for flakiness later.

## Migration needed
`session_token` is a new nullable column with no backfill requirement
(lazily generated on next login), so this is about as simple as a
migration gets. On the machine with the real database:
```
flask db migrate -m "add session_token to users"
flask db upgrade
```
Letting Flask-Migrate autogenerate this rather than hand-writing it
avoids guessing the correct `down_revision` — same reasoning as the
`link_url` migration earlier this week.

## Verification
- Full suite: 555/555 passing (542 baseline + 13 new tests: 1 ProxyFix
  regression test, 2 review-gate tests, 2 password-reset session tests,
  1 change-password self-logout test, 7 unit-level `get_id()`/`load_user()`
  tests).
- The ProxyFix test and the two RecursionError/g-caching bugs above
  were all caught *by writing and running the tests*, not assumed
  correct from reading the code — each one reproduced the failure
  first, then confirmed the fix resolves it.
