# Activity log

Reverse-chronological log of working sessions. One entry per session,
newest first. Details for each fix live in their own kebab-case doc.

## 2026-07-14 — Pre-deploy bug-hunt and production-readiness pass

Baseline: 539 passed; final: 539 passed. Re-swept the two bug classes
from the 07-12 pass, reviewed the new user-notification feature, and ran
the production-readiness checklist ahead of this week's deploy. Fixes
(each has its own doc):

- packages-mobile-filter-hide-specificity.md — mobile media query's
  display:none on #btn-clear / .active-filter-pill lost to an inline
  style and a higher-specificity .visible rule; desktop controls leaked
  into the mobile toolbar.
- notification-badge-nine-plus-unreachable.md — badge count is capped at
  9 by inject_notifications, so the template's '9+' branch never fired;
  20 unread showed as an exact-looking "9".
- visa-form-false-success-on-validation-failure.md — visa assistant
  modal treated plan_my_trip's 200 re-render (validation failure) as
  success; users saw "request sent" with nothing saved.
- mobile-sheet-continent-label-stale.md — mobile sheet's continent
  dropdown label hardcoded "All continents" even when a continent filter
  was active on page load.

Checked and clean: script-load-order class (initCustomSelect calls all
deferred behind DOMContentLoaded; packages.js only loaded where its DOM
exists), notification try/except isolation in add_package/visa_add
(creation commits before notifications, failures roll back and log),
link_url vs inquiry-based notification rendering (no collision), debug-
flag behavior (config only; 404/500/429 handlers present), no hardcoded
localhost/http URLs, SITE_URL consumed defensively everywhere, exactly
one migration head (bbb3d2515fa7), flake8/mypy/pylint (no real bugs).

Flagged, not fixed: per-user notification INSERT loop scales linearly
with the user table; Flask-Limiter uses in-memory storage (per-worker
limits under gunicorn); Dockerfile workers=4 and python:3.11 base both
pending the Render tier decision; bandit still broken against the
Python 3.14 venv (skipped by agreement).

## 2026-07-12 — Full bug-hunt, fix, and test pass

Baseline: 537 passed. Swept the whole app for two known bug classes plus
general issues. Fixes (each has its own doc):

- user-delete-auth-token-cascade.md — PasswordResetToken /
  EmailVerificationToken missing cascade; deleting a user with a reset
  token 500'd. Models fixed, regression tests added.
- blog-list-pagination-missing.md — blog paginated at 10/page but had no
  pagination UI; older posts unreachable.
- visa-hero-reduced-motion-opacity.md — inline opacity vs reduced-motion
  media rule (the known CSS specificity bug class).
- visa-edit-validation-order-pdf-loss.md — failed validation after PDF
  replacement deleted the live PDF file.
- package-delete-orphaned-files.md — package delete leaked flier and
  gallery files in storage.
- gallery-image-duplicate-order.md — multi-image gallery upload gave all
  new images the same order value.
- testimonial-review-selectinload-n-plus-one.md — selectinload added to
  three testimonial/review queries.

Checked and clean: script-order bug class (all external-function calls in
templates are wrapped or event-driven), migration heads (exactly one),
timezone handling (app code consistently uses datetime.now(timezone.utc)),
flake8/mypy/pylint (no runtime bugs; pylint func.count E1102s are false
positives). Note: bandit is listed in requirements but not installed in
the venv.
