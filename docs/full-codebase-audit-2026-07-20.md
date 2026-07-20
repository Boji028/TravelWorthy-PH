# Full codebase audit — Phase 1 findings

Date: 2026-07-20
Scope: entire `fixed/` app (backend, templates, CSS/JS, scripts, dead code).
Read-only audit — nothing in this report has been fixed yet.

This codebase already has ~130 prior fixes logged in `docs/`. Every finding
below was checked against that history first; anything already covered by an
existing doc is not repeated here unless the fix turned out to be incomplete
(noted explicitly where that's the case).

---

## Security

### S1. Email header injection guard exists but is never called
**File:** `email_service.py:8-10` (function `_strip_headers()`), used nowhere.
`InquiryForm.destination` (`forms.py`, `Length(min=2, max=200)`) has no
`Regexp` excluding CR/LF, and values like `inquiry.destination` are
interpolated straight into outgoing email `Subject` lines (e.g.
`email_service.py:59`, `:88`). A purpose-built sanitizer for exactly this
was written and then never wired into the send path.
**Severity: security (plausible, not confirmed exploitable)** — flagging
because the presence of an unused, purpose-built mitigation function is a
strong signal the gap is real, but I did not attempt to actually construct
and send a CRLF-bearing subject to confirm current `smtplib`/`email`
library behavior would allow it through.

---

## Backend bugs

### B1. `notification_service.py` is missing 5 of its 6 functions — a live regression
**File:** `notification_service.py` (24 lines; only `notify_inquiry_status_change` remains).
Commit `ccc94bd` ("feat: branded reply feature for contact messages in admin
panel" — an unrelated change) accidentally reverted this file, deleting
`notify_inquiry_created`, `notify_admins_new_inquiry`,
`notify_admins_inquiries_expiring`, `notify_users_new_package`,
`notify_users_new_visa`. Confirmed via `git show ccc94bd` diff and by
checking the file's current contents directly.

Every remaining caller of these names now hits `ImportError` at runtime:
- `routes/bookings.py:49,109` — new inquiry submissions (`plan_my_trip` and
  `inquire_package`) try to call `notify_inquiry_created`/
  `notify_admins_new_inquiry`; wrapped in `try/except Exception` (lines
  48-56, 108-116) that rolls back and logs a warning, so this fails
  **silently** — every inquiry submission since `ccc94bd` has produced zero
  in-app notifications for both the customer and admins.
- `routes/admin.py:375,1670` — `add_package`/`visa_add` call
  `notify_users_new_package`/`notify_users_new_visa`; also wrapped in a
  swallowing `try/except`, so `docs/notify-users-new-package-visa.md`'s
  entire feature is currently inert.
- `inquiry_cleanup_service.py:47,73` — `notify_admins_of_expiring_inquiries`
  calls `notify_admins_inquiries_expiring` with **no surrounding
  try/except**; this propagates up through `scripts/run_inquiry_cleanup.py`,
  which logs an error and exits 1. The admin "inquiries about to be
  auto-deleted" warning never fires on any scheduled run.
- `tests/test_notifications.py:107,120,155,178,191,214,227,243` import these
  same missing names directly and would fail.

**Severity: bug (high — live regression affecting three shipped features).**
This is the single most impactful finding in this audit.

### B2. `routes/admin.py::testimonials()` — N+1 not covered by the prior selectinload fix
**File:** `routes/admin.py:1772` — `base_query = Testimonial.query.join(User, Testimonial.user_id == User.id)`.
This `join()` is used only to filter/search; it does not populate the ORM
relationship (no `contains_eager`/`joinedload`/`selectinload`).
`templates/admin/testimonials.html:187,193,194` then reads
`testimonial.user.name` / `testimonial.user.email` per row (up to 20
rows/page via `paginate(...)`), firing one extra lazy-load query per row.
`docs/testimonial-review-selectinload-n-plus-one.md` fixed this exact shape
for `main.reviews`, `main.home`, and `packages.package_detail` but didn't
cover this admin route.
**Severity: bug (performance / N+1).**

### B3. Misleading comment on `reply_to_inquiry`
**File:** `routes/admin.py`, around the block that calls `send_inquiry_reply`
(~line 1008-1012). Comment says "Send email FIRST — do not commit until we
know it succeeded", but the return value of `send_inquiry_reply(...)` is
discarded — nothing here actually checks success.
`docs/fix-silent-inquiry-email-failures.md` documents that only
`send_inquiry_receipt()`'s return value is checked and this call site is
intentionally left as-is, so the *behavior* is a known, accepted limitation
— but the comment overstates what the code does and could mislead whoever
touches this next.
**Severity: minor.**

---

## Dead code — backend

### D1. `models/admin.py` — a 2,325-line orphaned duplicate of `routes/admin.py`
Confirmed via `diff routes/admin.py models/admin.py` and
`grep -rn "models\.admin"` (zero hits anywhere in the repo; not imported by
`models/__init__.py` or anything else). It's an older snapshot of
`routes/admin.py` from before the Contact Us feature was removed — it still
contains the five contact-message routes and the `ContactMessage` import
that `docs/remove-contact-messaging-feature.md` describes deleting from
the real file. Git history shows its only commit is `ccc94bd`, the same
commit that regressed `notification_service.py` (B1) — it looks like an
accidental stray write from that commit that was never caught.
**Severity: dead-code (large — whole file).**

### D2. Contact-messaging removal was only half-executed
`docs/remove-contact-messaging-feature.md` explicitly lists four files
under "Deleted files (won't be removed by extracting the zip — delete
manually)". All four are still present, verified directly:
- `models/contact.py`
- `templates/admin/contact_messages.html`
- `scripts/migrate_contact_user.py`
- `tests/test_contact_messages.py`

`tests/test_contact_messages.py` still imports `models.contact.ContactMessage`
and calls `/admin/contact-messages` routes that no longer exist in
`routes/admin.py` (they were removed per the doc, but only from the real
file — see D1) — this test file would currently fail if run.
**Severity: dead-code.**

### D3. Unused imports
- `routes/main.py:2` — `from typing import Union` — no `Union[...]` usage in the file.
- `routes/main.py:11` — `save_image_metadata` imported, never called.
- `routes/main.py:230` — local `from datetime import datetime` inside `sitemap()` is unused (only `.strftime()` is called on existing datetime objects).
- `routes/auth.py:2` — `Union` unused.
- `routes/packages.py:2` — `Dict, Any` unused (`Union` at line 39 is used).
- `routes/admin.py:2` — `Union, Dict, Any` unused.
- `routes/admin.py:16` — `compress_image` imported from `utils`, never called (superseded by `ImageUploadService.upload_and_compress`).
- `email_service.py:8-10` — `_strip_headers()` defined, never called (see S1).
**Severity: dead-code / minor.**

### D4. `scripts/` folder — mostly legitimate, one confirmed orphan
Cross-referenced every script against `docs/` and each other's docstrings.
All scripts are legitimate standalone maintenance/migration tools **except**:
- `scripts/migrate_contact_user.py` — dead per D2 (docs say delete manually, never was).
`delete_dummy_test_inquiries.py`, `diagnose_inquiry_cleanup.py`, and
`seed_dummy_expiring_inquiries.py` aren't named in any doc by filename but
reference the inquiry auto-delete feature and each other in their own
docstrings — legitimate, just undocumented by name, not orphaned.
**Severity: dead-code (one file).**

---

## Frontend bugs — CSS specificity

### F1. Duplicate `.nav-links a:hover` rule — `!important` amber silently wins over intended teal
**File:** `static/css/main.css:58-61` and `:167-170`.
```css
58: .nav-links a:hover { box-shadow: 0 0 15px var(--amber); color: var(--amber) !important; }
...
167: .nav-links a:hover { background: var(--linen); color: var(--teal); }
```
The rule at line 58 predates the later dark/light nav rework and was never
removed. Because it uses `!important`, it always wins on `color` regardless
of the later, unqualified rule at line 167 that was clearly meant to be the
real one — nav links glow amber on hover instead of teal. Same bug class as
the already-fixed `.nav-logo span` issue (a stale broad/forceful rule
clobbering a later, more-intended one), just a different pair of rules.
**Severity: bug.**

No other live instances of the "broad descendant selector clobbers a nested
child's intended color" shape were found — `.footer-brand span`,
`.logo-card span`, `.dest-tile span`, `.sidebar-price span`, `.tw-tile .lbl
b/small`, `.pkg-mi i`, `.mobile-sheet-header span` were all checked and only
wrap single, non-conflicting children.

---

## Frontend bugs — overflow / responsive

### F2. `.inquiries-table-wrap` only gets `overflow-x: auto` on mobile — desktop/tablet has no scroll safety net
**File:** `templates/admin/inquiries.html:322-326` — `overflow-x: auto` is
scoped inside `@media (max-width: 768px)` only; there's no unconditional
base rule. A long customer email in `.cust-email` (~line 428-429) has
nothing to fall back on above 768px width. Contrast with
`admin/users.html:197` (inline `style="overflow-x:auto"`, unconditional)
and `admin/contact_messages.html:291-293` (unconditional rule) — both
correct; `inquiries.html` is the one page where this got scoped to
mobile-only by mistake.
**Severity: bug (minor/moderate).**

### F3. Native date inputs still missing the `dstack`/`doverlay` iOS fix in three places
Per `docs/date-input-still-oversized-ios-safari.md`, a font-family-only fix
was proven insufficient on real iOS Safari, and the `dstack`/`doverlay`
pattern was introduced to replace it everywhere — but three spots were
missed:
- **`templates/bookings/plan_my_trip.html:340,348`** — both date inputs are
  plain `<input type="date" class="form-control">`, not wrapped in
  `dstack-input`/`doverlay`. This was the exact file called out as a likely
  remaining offender; confirmed.
- **`templates/admin/inquiries.html:394,396`** — date filter inputs use only
  `.inq-toolbar input[type="date"]` sizing rules (font-size/padding/border);
  no font-family reset, no dstack wrapping.
- **`templates/main/home.html:293`** — the hero search's `#twDepReal` date
  input has no `class="form-control"` at all, so it doesn't even get the
  existing `input[type="date"].form-control` font-family reset. `.tw-sf
  input { font-family: inherit; }` (home.html:71) means it inherits the
  page's display font — the original root cause described in
  `docs/fix-date-input-sizing-mobile.md`. It uses a `color:transparent` +
  overlay-text trick, but that only masks the text color, not the native
  control's box sizing — the documented iOS shell-sizing bug isn't
  addressed here.

Confirmed NOT offenders (already correct): `packages/visa.html`,
`packages/detail.html`, `bookings/inquire_package.html` all use
`dstack-input` correctly; `admin/add_package.html`/`edit_package.html` have
no date inputs at all.
**Severity: bug (3 locations).**

### F4. Admin form grids have zero mobile breakpoints
**Files:** `templates/admin/add_package.html:14-18`,
`templates/admin/edit_package.html:14-18` — `.form-row { display:grid;
grid-template-columns: 1fr 1fr; }` has no `@media` query anywhere in either
file (confirmed 0 occurrences of `@media`). The public-facing equivalents
(`bookings/plan_my_trip.html:181-183`, `bookings/inquire_package.html:118-120`)
both correctly stack to one column at ≤768px — these two admin templates
were never given the same treatment. One cramped row holds a currency
`<select style="width:130px">` next to a price input
(`add_package.html:143-150`), which will be squeezed on the admin mobile
sidebar-drawer view that `docs/add-admin-mobile-sidebar-drawer.md` added
support for.

Same gap, more severe (inline styles, can't even add a breakpoint without
refactoring to a class first): `admin/add_visa.html`, `admin/edit_visa.html`,
`admin/add_country.html`, `admin/edit_country.html` — all use inline
`style="display:grid;grid-template-columns:1fr 1fr"` (or `1fr 1fr 1fr`)
directly on the element, 0 `@media` anywhere in any of these files.
**Severity: bug (6 files).**

Not a bug: `main/about.html` grids (`.about-values`, `.service-list`,
`.dest-grid`, `.why-grid`, `.logo-grid`) are all correctly covered — the
`.why-grid` 768px stacking rule exists in code even though
`docs/fix-about-page-mobile-grids.md` doesn't mention it (doc is stale,
code is fine).

---

## Frontend — dead / inert features

### F5. Lightbox markup is fully wired for closing but nothing ever opens it
**File:** `templates/packages/list.html:977-980` (markup) +
`static/js/packages.js` (`openLightbox(src)` + its DOMContentLoaded
listener on `#lightbox-img`). `openLightbox(...)` is never called from any
template or inline `onclick`. The close button/backdrop click handlers
work, but there's no code path that ever opens the lightbox — an inert,
half-built feature.
**Severity: dead-code / minor bug (dead feature, not actively harmful).**

### F6. Dead CSS classes — defined, never referenced
Cross-checked every class below against `class="..."` usage in all
templates and `classList`/`querySelector` usage in JS. None found live:

- `static/css/main.css:38-56` — `.btn-hero-primary`, `.btn-hero-ghost` (pre-dark-mode leftovers).
- `static/css/main.css:526-529` — `.badge-pending`; `:536-539` — `.badge-cancelled`. `Inquiry.VALID_STATUSES` (`models/inquiry.py:14`) is `{"new","contacted","confirmed","closed"}` — the only dynamic-class site (`admin/dashboard.html:358`, `badge-{{ inq.status }}`) can never produce "pending" or "cancelled", so these are unreachable.
- `static/css/main.css:202-208` — `.nav-user`; `:563-569` — `.section-title`; `:571-575` — `.section-sub`.
- `templates/packages/detail.html:470-591` — `.rating-summary`, `.big-rating`, `.big-rating-stars`, `.big-rating-count`, `.rating-bars`, `.rating-row`, `.rating-label` (class form), `.rating-bar-bg`, `.rating-bar-fill`, `.rating-num`, `.rv-top`, `.rv-av`, `.rv-name`, `.rv-date`, `.rv-stars`, `.rv-text` — all dead; matches the exact class of bug already found once in this file (`.rating-bars` etc.) but this is a *different, larger* set of classes than what was already fixed — the actual review UI (~lines 1140-1176) uses inline `style=""` instead.
- `templates/packages/detail.html:631-683` — `.date-grid`, `.date-cell`, `.guests-field` — same pattern; the real booking sidebar (lines ~1126, 1417) uses inline-styled grids instead.
- `templates/auth/login.html:29-51`, `templates/auth/forgot_password.html:29-40` — `.auth-brand .logo-icon` dead; both pages render a plain `<img>` instead.
- `templates/auth/login.html:53-66` — `.auth-divider` dead; the divider (lines 113-117) uses inline-styled `<div>`s.
- `templates/admin/add_package.html:14-18`, `templates/admin/edit_package.html:14-18` — `.form-card .sub` dead in both (no `class="sub"` present), unlike the booking templates which do use `<p class="sub">`.
- `templates/admin/inquiries.html:88-94` — `.inq-toolbar-label` dead.
- `templates/main/reviews.html:224` — `.submit-section` dead.
- `templates/main/about.html:6` — `.mvt-card p` dead; `.mvt-card` itself is never applied to any element.

**Severity: dead-code (many small instances).**

Not dead (checked, confirmed live): `.quick-link` (`auth/profile.html:43`),
`.track-step` (`main/inquiry_status.html:78`) — flagged initially as
possible grid-overflow risks but only ever contain short/wrappable text, so
not a real instance of the `1fr`-without-`min-width:0` bug. `initCustomSelect`
and `initDateDisplay` in `main.js` are both called from templates — not dead.

---

## Not flagged — checked and found solid

- Every `NOT NULL` FK relationship reviewed
  (`EmailVerificationToken`, `PasswordResetToken`, `PackageReview`,
  `Testimonial`/`TestimonialImage`, `InquiryNotification`) correctly uses
  `cascade='all, delete-orphan'` or `passive_deletes=True` per the
  CLAUDE.md pitfall.
- IDOR: `main.my_inquiries`, `main.mark_notification_read`, `auth.profile`,
  and both `bookings.py` routes are all correctly scoped to
  `current_user.id`. `track_inquiry` (lookup by reference number, no
  login required) is an intentional "anyone with the reference number can
  view" trust model, same as a parcel-tracking number — not an IDOR.
- Rate limiting on login/register/forgot-password/inquiry-submission
  matches the current, deliberate scope already described across
  `rate-limit-login-route.md`, `scope-rate-limits-to-auth-and-inquiry-routes.md`,
  `auth-rate-limit-scoped-to-post.md`. `register`'s reliance on the global
  default limiter only is already flagged-and-deferred in those docs, not
  a new gap.
- No `|safe` filter usage found anywhere in `templates/`.
- `delete_user`/`delete_agent` reference `.name` in a flash message after
  `db.session.delete()` + `commit()` — looked like a potential
  expired-instance access bug, but detached SQLAlchemy instances keep
  already-loaded attributes cached in memory; confirmed safe via
  `tests/test_cascade_deletes.py` passing.
- `backup_service.py`/`backup_scheduler.py` — `create_backup()` fully wraps
  subprocess/file I/O in try/except and never re-raises, so a single failed
  backup can't crash the scheduler loop.
- No other unmitigated `1fr`/`flex:1` grid-overflow instances found beyond
  what's already fixed.
- No new literal copy-paste text-duplication bugs found (footer "PH" bug
  already fixed and confirmed via `git show`). Two apparent duplicate `id`
  attributes (`packages/detail.html`, `admin/edit_blog.html`) are both
  inside mutually exclusive `{% if/elif/else %}` branches and never
  co-render — not a real bug.

---

## Summary table

| # | File(s) | Finding | Severity |
|---|---|---|---|
| S1 | `email_service.py` | Header-injection guard defined, never called | security (plausible) |
| B1 | `notification_service.py` + 4 call sites + tests | 5 of 6 functions missing — live regression, 3 features silently broken | bug (high) |
| B2 | `routes/admin.py:1772` | Testimonials admin page N+1 not covered by prior fix | bug (perf) |
| B3 | `routes/admin.py` ~1008 | Comment overstates error handling | minor |
| D1 | `models/admin.py` | 2,325-line orphaned duplicate file | dead-code |
| D2 | 4 files (contact.py, contact_messages.html, migrate_contact_user.py, test_contact_messages.py) | Contact-removal cleanup never executed | dead-code |
| D3 | 8 import sites | Unused imports | dead-code/minor |
| D4 | `scripts/migrate_contact_user.py` | Orphaned script | dead-code |
| F1 | `main.css:58-61` vs `:167-170` | Duplicate `.nav-links a:hover`, `!important` wins wrong color | bug |
| F2 | `admin/inquiries.html:322-326` | Overflow-x scoped to mobile only | bug (minor) |
| F3 | `plan_my_trip.html`, `admin/inquiries.html`, `main/home.html` | 3 date inputs missing dstack/doverlay iOS fix | bug |
| F4 | 6 admin templates | Zero mobile breakpoints on form grids | bug |
| F5 | `packages/list.html` + `packages.js` | Lightbox can close but never opens | dead-code/minor |
| F6 | `main.css` + 8 templates | ~25 dead CSS classes across the codebase | dead-code |

---

## Open questions for Phase 2 prioritization

1. **B1** (notification regression) is the clear top priority — it's an
   active, silent, three-feature production bug, not a hypothetical. Given
   it stems from an accidental revert, the fix is to restore the four
   missing functions from `git show ccc94bd~1:notification_service.py`
   (the pre-regression version) rather than rewrite them from scratch —
   want me to do it that way?
2. **D1** (`models/admin.py`) — confirmed zero references anywhere, safe to
   delete outright. Will do as a `remove:` commit unless you want to
   double-check first given its size.
3. **S1** (email header injection) — I'm not fully confident this is
   exploitable without testing against the actual mail backend in use. If
   you want this fixed regardless of confirmed exploitability (defense in
   depth — wire `_strip_headers()` into the subject-building calls), say so;
   I won't guess on a security item.
4. **D2** — deleting these four files finishes work the boss already
   signed off on (`docs/remove-contact-messaging-feature.md` — "Boss's
   decision"), so this reads as low-risk cleanup rather than a new call,
   but flagging since it's file deletion.
