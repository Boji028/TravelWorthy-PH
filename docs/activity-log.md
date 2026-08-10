# Activity log

Reverse-chronological log of working sessions. One entry per session,
newest first. Details for each fix live in their own kebab-case doc.

## 2026-08-10 — Wishlist / save-for-later feature

Baseline: 571 passed; final: 594 passed (23 new tests, 0 failed). New
feature: logged-in users can save a tour package or a visa country entry
to a personal wishlist via a heart-toggle icon, and review/remove saved
items from a new "My Wishlist" page. Built in three commits plus one
browser-verification fix:

- **`b1deba9`** — `models/wishlist.py` (`WishlistItem`) + migration.
  **Design decision:** a single table with nullable `package_id`/`visa_id`
  FKs and a `CheckConstraint` enforcing exactly one is set per row, rather
  than two separate join tables. No existing model in this codebase
  already solves "one row references one of several content types"
  cleanly — `Inquiry` fakes it by string-sniffing `special_requests` for
  `"[FOR VISA]"`, which is a known anti-pattern, not something to copy.
  Given a genuinely fresh choice, the single-table shape was picked
  because `Inquiry.__table_args__` already established
  `db.CheckConstraint(...)` as a tested idiom in this repo — extending it
  to "exactly one of two FKs" is a small, consistent step rather than a
  new concept, and it means one route/template/JS path covers both
  content types instead of duplicating everything twice. Consequence:
  because the constraint requires exactly one FK non-null, a nullable FK
  alone isn't sufficient for safe deletes — `cascade='all, delete-orphan'`
  is needed on all three parent sides (`User`, `TourPackage`,
  `VisaCountry`), not just `User`, or deleting a package/visa with saved
  items would null out one FK and leave both null, violating the
  constraint (the same class of bug CLAUDE.md's cascade pitfall warns
  about, just via a CHECK violation instead of a NOT NULL violation).
- **`bb2e19a`** — `routes/wishlist.py` (toggle-package, toggle-visa,
  my_wishlist page) + saved-state wiring into `routes/packages.py`'s list/
  detail/visa views. The toggle routes deliberately skip
  `@login_required`: this app has no existing pattern for an AJAX action
  that requires login (every current login-gated route just does a
  full-page redirect), and a logged-out `fetch()` would silently receive
  a followed redirect's HTML instead of an error it can act on. Each
  route checks `current_user.is_authenticated` itself and returns a real
  401 with a `login_url` instead.
- **`224d62f`** — heart icons on package cards, the package detail page,
  and visa cards; the new "My Wishlist" page; nav links. `static/js/
  wishlist.js`'s fetch handler explicitly branches on a 401 status before
  parsing JSON, which sidesteps a real, pre-existing bug of the same
  shape already sitting in `templates/main/reviews.html`'s delete handler
  (it treats a followed login-redirect as success via `res.redirected`).
- **`fbc7d22`** — two fixes found only by actually running the app in a
  browser (Playwright driven against the local dev server), not by
  pytest: the visa-card heart was positioned right where the country flag
  flows into the header band, partially hiding it — moved into the card's
  content section instead. Removing the last item in a wishlist section
  via its own heart icon left a blank box with no "nothing saved yet"
  message, since that fallback was only ever rendered server-side at page
  load — `wishlist.js` now adds it back in client-side when a section
  empties out.

Per your answers during planning: no separate visa "detail page" exists
in this codebase (routes/packages.py's `visa()` renders one listing
template with cards + two JS modals, never a per-country page), so the
heart only went on visa cards, not into the PDF-requirements modal.
Logged-out heart clicks redirect to `/auth/login?next=<page>`, matching
how every other login-gated link in this app already behaves.

## 2026-08-10 — Dead-code cleanup from the 2026-07-20 audit's deferred list

Baseline: 571 passed; final: 571 passed (unchanged throughout - pure
dead-code removal, no behavior changed). Scope was strictly the four items
docs/full-codebase-audit-2026-07-20.md flagged as dead code but left
unactioned (D3, D4, F5, F6); nothing else in that audit was touched. Each
category got its own commit and its own full test run before moving on:

- **Unused imports (D3)** — `9a23be7`. Removed `typing.Union` from
  routes/main.py and routes/auth.py; `typing.Dict`/`Any` from
  routes/packages.py and routes/admin.py (`Union`/`Optional` are still
  used in each, kept); the unused `utils.save_image_metadata` import from
  main.py (admin.py's copy is genuinely used across 9 call sites - kept
  there); the dead local `from datetime import datetime` inside main.py's
  `sitemap()`; and `utils.compress_image` from admin.py. Skipped
  `email_service.py`'s `_strip_headers()`, which was on the audit's D3
  list: it's a function definition, not an import, and it's since been
  wired into `_send()` (commit `5657aac`) so it's live code now, not dead.
- **Orphaned script (D4)** — no commit needed. `scripts/migrate_contact_user.py`
  was already deleted the same day as the audit (commit `8f89c68`, part of
  the separate D2 contact-messaging cleanup). Confirmed via `git log` and a
  repo-wide search before concluding there was nothing left to remove.
- **Inert lightbox feature (F5)** — `4341ec9`. Removed the dead
  `#lightbox` markup/CSS from templates/packages/list.html, its
  `<script src="packages.js">` tag, and deleted static/js/packages.js
  outright (100% of its content was the dead openLightbox/closeLightbox/
  zoom-toggle code, nothing else in the file). templates/main/reviews.html
  has its own separate, fully-wired lightbox (own `<style>`/`<script>`,
  different function signature, never loads packages.js) - confirmed
  unrelated and left untouched.
- **~25 dead CSS classes (F6)** — `d8e0be0`. Removed across
  static/css/main.css (7 classes) and 7 templates (detail.html,
  login.html, forgot_password.html, add_package.html, inquiries.html,
  reviews.html, about.html). Full list in the commit message. Re-verified
  every class fresh against current templates/JS rather than trusting the
  audit's line numbers, since a lot of unrelated CSS/mobile work has
  landed since 2026-07-20.

Verified-and-kept (audit was stale here): edit_package.html's copy of
`.form-card .sub` no longer exists - already cleaned up in a prior commit
since the audit was written, so there was nothing to remove there.
`email_service.py`'s `_strip_headers()` - see D3 above.

Not evaluated this session (outside scope, not touched): the audit's
remaining open items. B1, D1, D2, S1 were already resolved same-day as the
audit (2026-07-20, before this session started); F1-F4 (CSS specificity,
overflow, date-input, and mobile-grid bugs) were not part of this cleanup
and were left alone.

Not pushed - commits are local on main pending review.

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

## 2026-07-15 — Fresh-eyes sweep of the post-journey-pass work

Baseline: 561 passed. Focus: the mechanisms added since the last full
sweep (ProxyFix, session_token, review gate, confirmation_email_failed,
notifications) plus a general routes/models/services read-through.

Fixes (each has its own doc):

- auth-rate-limit-scoped-to-post.md — forgot-password / resend-
  verification 5/hour limits applied to GET page views (keyed by IP on
  GET); five page loads locked out a shared IP. Scoped to POST.
- inquiry-list-export-package-n-plus-one.md — inq.package.title lazy-
  loaded per row on the admin inquiries list (bounded) and xlsx export
  (unbounded). joinedload added to both.
- geo-edit-blank-name-validation.md — edit_continent/edit_country
  accepted a blank name that add_* rejects; saved an empty string.
- inquiry-confirmed-email-eager-host-url.md — send_inquiry_confirmed
  evaluated request.host_url eagerly as a .get() default; latent crash
  if ever called off-request. Switched to the guarded `or` form.

Checked and clean: migration heads (one: 3cee47dfc5ac); the three
templates touched this week introduced no new inline scripts and no
inline styles competing with media queries; _external=True still only
the three known call sites (template og:image uses go through url_for,
ProxyFix-covered); every login path goes through login_user() so
session_token coverage is complete; review eligibility has a single
enforcement point (_can_review_package; the /reviews page is the
separate Testimonial feature); flake8 F82x/E9 clean, pylint/mypy only
the known false-positive patterns.

Flagged, not implemented (design call): the inquiry xlsx export does
not include confirmation_email_failed, so a failed confirmation isn't
visible in the exported follow-up record.
