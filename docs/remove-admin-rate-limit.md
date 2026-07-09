# Remove overly restrictive rate limit blocking admin content creation

## Problem
Adding packages (and blog posts, visa entries) in the admin panel
started returning "429 Too Many Requests - 10 per 1 hour" after normal
use - not abuse, just adding several packages in one session.

## Root cause
Five admin routes had `@limiter.limit("10 per hour")` stacked on top
of `@admin_required`: `add_package`, `add_blog`, `edit_blog`,
`visa_add`, `visa_edit`. All five are already gated by
`@admin_required`, which chains `@login_required` (redirects
unauthenticated requests) and then checks `current_user.is_admin` -
a complete authentication + authorization boundary on its own. Only a
logged-in admin account can ever reach these routes, so there's no
anonymous-abuse vector for the rate limit to guard against here -
unlike, say, the public contact form or inquiry submission, where a
10/hour cap makes real sense against bot spam.

The limit was also applied inconsistently: other admin content routes
like `add_continent`, `add_country`, and `add_agent` have no rate
limit at all. That inconsistency, combined with the limit being
copy-paste-identical across all five ("10 per hour", verbatim) rather
than tuned per-route, suggests it was carried over from a public-form
pattern rather than a deliberate policy for authenticated admin work.

## Fix
`routes/admin.py`: removed `@limiter.limit("10 per hour")` from all
five routes, keeping `@admin_required` as the sole (sufficient) gate.
Also removed the now-unused `limiter` import (`from app import db,
limiter` -> `from app import db`), since nothing in this file
references it anymore.

## Immediate workaround (while waiting for this fix to be applied)
Flask-Limiter is running on in-memory storage in this project (the
startup warning confirms it), so the request counter resets on
restart. Stopping and restarting `python run.py` clears the limit
immediately without waiting out the full hour.

## Verification
- Confirmed zero remaining `@limiter.limit` calls in `routes/admin.py`
  and all five function definitions still intact.
- Paren balance on the file: 1431/1431 matched.
- `flake8 --select=F401,F821`: no undefined-name errors (confirms
  `limiter` truly has no remaining references), and the F401 warnings
  present are pre-existing, unrelated to this change.
- Full test suite: 512/512 passing.

No migration needed - two lines removed per route, one import
trimmed.
