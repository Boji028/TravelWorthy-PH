# Scope rate limits to auth + contact/inquiry submission routes only

## Problem
Per-route rate limits had accumulated on several routes over time
without a consistent policy — some on genuine abuse vectors (auth,
public form submissions), others on routes where they didn't add real
protection (a logged-in user's testimonial submission, a public
read-only inquiry tracker, and the packages browsing/AJAX routes,
which had already been loosened to 60/minute earlier this month just
to stop real users from tripping them during normal filtering).

Also, hitting any limit returned Flask-Limiter's bare default 429
response — no styling, no explanation, inconsistent with the site's
branded 404/500 pages.

## Decision
Rate limiting is most valuable where it stops real attacks: brute-force
login/credential guessing and token-guessing. It's secondary insurance
elsewhere. Scoped limits down to exactly two categories:

1. **Auth flows** - guards against brute-force and token/email-guessing.
2. **Public form submissions that send email and write to the DB**
   (contact form, inquiry submission) - guards against bot spam that
   would cost mail-quota and inbox noise.

## Fix
Removed `@limiter.limit(...)` from:
- `routes/main.py`: `add_testimonial` (was 5/hour) - already behind
  `@login_required`, and a real user can only ever submit one
  testimonial (enforced by the existing `existing =` query), so a
  rate limit added nothing.
- `routes/main.py`: `track_inquiry` (was 30/minute) - this is a
  read-only status lookup, not a submission; the reference number is
  already unguessable (6-char random hex), same trust model as a
  parcel tracking code.
- `routes/packages.py`: `list_packages`, `package_detail`,
  `autocomplete` (all 60/minute) - public browsing routes, no
  submission/abuse vector. Also removed the now-unused `limiter`
  import (`from app import db, limiter` -> `from app import db`) and
  a stale docstring line on `autocomplete` referencing the removed
  limit.

Kept `@limiter.limit(...)` on:
- `routes/auth.py`: `resend_verification`, `forgot_password` (5/hour
  each, keyed by submitted email rather than IP)
- `routes/main.py`: `contact` (10/hour on POST)
- `routes/bookings.py`: `plan_my_trip`, `inquire_package` (10/hour on
  POST each) - the actual inquiry-submission routes

Note: `login` and `register` have no dedicated per-route limit either
before or after this change - they're covered only by the app-wide
default (`300 per day / 60 per hour / 10 per minute` in `app.py`,
applied to every non-exempt route). Worth a dedicated stricter limit
on `login` specifically if brute-force protection there needs to be
tighter than the global default - flagging this, not changing it here
since it wasn't part of the requested scope.

## UX improvement
Added a branded 429 page (`templates/429.html`), matching the
existing `404.html`/`500.html` pattern exactly (same teal number,
`--mist` body copy, amber button). Registered via
`@app.errorhandler(429)` in `app.py`, right after the existing 500
handler. Applies globally, so it also covers the app-wide default
limit tripping on any route, not just the five listed above.

## Verification
- Confirmed exactly five `@limiter.limit` decorators remain sitewide
  (grep across `routes/`), matching the list above.
- Both edited route files parse cleanly (`ast.parse`).
- Full test suite: 529/529 passing.

No migration needed - decorator removals, one import trim, one new
template, one new error handler.
