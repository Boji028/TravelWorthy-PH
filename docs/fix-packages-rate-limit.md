# Give the public packages browsing routes their own rate limit

## Problem
Browsing `/packages/` (and clicking into a package's detail page) started
returning "429 Too Many Requests - 10 per 1 minute" during completely
normal use - filtering by continent/type, paging through results, or
opening a couple of package cards in quick succession.

## Root cause
`app.py` sets a global `default_limits=["300 per day", "60 per hour",
"10 per minute"]` on the Limiter instance. Any route with no explicit
`@limiter.limit(...)` of its own falls under this default. `list_packages`
and `package_detail` never had their own limit, so they were capped at 10
requests/minute total.

This was fine back when the page was a handful of full-page navigations,
but the packages page now does a real AJAX-driven filtering UI (continent
tabs, country chips, type toggle, destination search, pagination, and the
new mobile filter sheet) - every tap is its own request. A normal
filtering session (open the mobile sheet, tap a region, tap a country,
tap Apply, then page through results) blows past 10 requests in well
under a minute, same failure mode as the admin rate limit bug fixed
earlier, just on a public route instead of an admin one.

`routes/packages.py::autocomplete` already carries its own
`@limiter.limit("60 per minute")` for exactly this reason - it just never
got extended to the two routes that actually needed it most once the
filtering UI got built out.

## Fix
`routes/packages.py`: added `@limiter.limit("60 per minute")` to
`list_packages` and `package_detail`, matching the limit `autocomplete`
already uses. The global default (10/minute) still applies to every other
unguarded route, so this only loosens the two routes that legitimate
interactive browsing actually hits repeatedly.

## Immediate workaround (while waiting for this fix to be applied)
Flask-Limiter is running on in-memory storage in this project, so the
request counter resets on restart. Stopping and restarting `python run.py`
clears the current 429 immediately without waiting out the full minute.

## Verification
- Full suite: 522/522 passing.
- No dedicated rate-limit test added - same as the earlier admin rate
  limit fix, the existing suite has no rate-limit-triggering tests
  (would need 61+ requests in one test to actually trip the old limit,
  which is slow and fragile) and the fresh-app-per-test fixture already
  exercises multiple requests per test file without issue at the new
  ceiling.

No migration needed - two decorator lines added.
