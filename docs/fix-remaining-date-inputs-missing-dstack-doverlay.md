# Fix 3 remaining native date inputs missing the dstack/doverlay iOS fix

## What was wrong
`docs/date-input-still-oversized-ios-safari.md` established that a plain
font-family reset isn't enough to fix iOS Safari's refusal to honor CSS
sizing on native `<input type="date">` — the `dstack`/`doverlay` pattern
(real input made fully invisible and absolutely positioned; a plain
sibling div renders the visible box) was rolled out to replace it. Three
date inputs were never migrated:

- `templates/bookings/plan_my_trip.html:340,348` — plain
  `<input type="date" class="form-control">`, no wrapping at all.
- `templates/admin/inquiries.html:394,396` — the date-range filter inputs
  had only small toolbar-specific box styling (font-size/padding/border),
  no font-family reset and no wrapping.
- `templates/main/home.html:293` (`#twDepReal`, the hero search's
  departure-date field) — used a bespoke `color: transparent` +
  marquee-overlay trick. That hides the input's text color, but the input
  stayed in normal document flow with no explicit sizing override, so
  iOS Safari's native picker shell could still render at its own
  OS-determined size regardless of the surrounding CSS — the same class
  of bug, just disguised by a different existing overlay mechanism.

## Fix
- **plan_my_trip.html**: wrapped both date inputs in the standard
  `dstack`/`doverlay` markup (`dstack-input` class, sibling `doverlay
  form-control` div), matching `bookings/inquire_package.html`. Added
  `initDateDisplay(...)` calls in a new `<script nonce="{{ csp_nonce()
  }}">` block wrapped in `DOMContentLoaded` (this file's existing inline
  script isn't itself wrapped, but it doesn't call any main.js function,
  so it doesn't need to be — the new one does, so it must wait for
  main.js, which loads after the content block in `base.html`).
- **admin/inquiries.html**: wrapped both filter date inputs in
  `dstack`/`doverlay` markup too, but admin pages don't load `main.js` at
  all (no other admin template uses this pattern or that script). Rather
  than add a new shared-JS dependency to the whole admin layout — which
  would also silently add main.js's unrelated public-site behaviors
  (flash auto-hide, mobile nav toggle) to every admin page — added a
  small self-contained `initDateOverlay()` function directly in this
  template's own script block, mirroring `main.js`'s `initDateDisplay()`.
  Also updated `applyDateMode()`'s clear-inputs logic to `dispatchEvent(new
  Event('change'))` after setting `.value = ''`, since a direct property
  assignment doesn't fire the `change` event the overlay listens for —
  without this, clearing the date range via the dropdown would leave the
  overlay showing a stale date.
- **main/home.html**: kept the existing marquee-overlay mechanism (already
  functionally equivalent to `doverlay` — it's already absolutely
  positioned and formats the date the same way via `twUpdateDep()`), but
  changed `input[type="date"]`'s CSS from `color: transparent` to fully
  invisible and absolutely positioned (`opacity: 0; position: absolute;
  inset: 0;`), scoped to a new `.tw-date-stack` modifier class on just
  this one field's wrapper (not the destination/guests fields, which
  aren't native date pickers and don't have this bug). Added `min-height:
  20px` to `.tw-date-stack` so the wrapper doesn't collapse to zero
  height once its only normal-flow child is taken out of flow — the
  overlay is `overflow: hidden`, so a collapsed wrapper would make the
  "Departure" label invisible.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding F3).

## Tests
No new automated tests — this is native-control rendering behavior on
iOS Safari specifically, which the Python/Jinja test suite can't exercise
(no real browser in this test setup). Ran the existing suites that touch
these three templates (`test_bookings.py`, `test_admin_inquiries.py`,
`test_public_pages.py` — 59 tests) to confirm form submission and
rendering still work; all pass.

**Manual re-check requested** (I can't visually verify rendering myself):
- `plan_my_trip.html` and `admin/inquiries.html`: low risk, direct reuse
  of an already-proven pattern — a quick look on any device confirms
  correct sizing.
- `main/home.html`: higher-attention item. This is the homepage hero
  search, and the fix changes layout mechanics (input taken out of flow,
  new min-height on the wrapper) rather than just adding a wrapper like
  the other two. Please check at minimum: iPhone Safari (the actual bug
  this fixes), plus a quick look at ~375px, ~768px, and ~1440px widths to
  confirm the "Departure" label still renders at its usual size/position
  and the date picker still opens correctly on tap.
