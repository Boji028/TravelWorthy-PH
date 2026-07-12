# Bring packages mobile filter animation up to parity with visa

## Context
Comparing the two pages side by side: `packages/visa.html` already had
a fully animated mobile filter experience — chip row scrolls
horizontally at 768px, and filtered cards replay a staggered rise-in
animation instead of snapping in via `display`. `packages/list.html`'s
mobile filter (the bottom sheet's region chip → country grid
expansion) had none of that: `.mobile-country-grid` toggled between
`display: none` and `display: grid` with zero transition, and
`.mobile-chip` / `.mobile-country-chip` had no transition on their
active-state color change either.

Note: this was purely a CSS gap in the one interaction that predates
the page's AJAX system. The actual data-changing filter action (tapping
Apply) already has solid animation — skeleton loading state, then a
staggered `pkgRise` fade-in per card once the AJAX response lands.
That part wasn't touched; it didn't need it.

## Fix
`templates/packages/list.html`, `.mobile-chip` / `.mobile-country-chip`:
added `transition: background .18s ease, color .18s ease, border-color
.18s ease;` so the active-state swap fades instead of snapping.

`.mobile-country-grid`: switched from a `display: none` / `display:
grid` toggle (which can't be transitioned at all — `display` isn't
animatable) to a `max-height` + `opacity` transition:
```
.mobile-country-grid {
  display: grid;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  pointer-events: none;
  transition: max-height .25s ease, opacity .2s ease, margin-top .25s ease;
}
.mobile-country-grid.open {
  max-height: 600px;
  opacity: 1;
  margin-top: .75rem;
  pointer-events: auto;
}
```
`max-height: 600px` is a generous fixed cap — well above any realistic
country list for a single continent — since `max-height` transitions
need a concrete target value, not `auto`. `pointer-events: none` on
the closed state is a small defensive addition: without it, the
(visually clipped but still-present) country chips could theoretically
still be tapped in some browsers before the collapse finishes.

No JS changes — `.mobile-country-grid`'s `open` class was already
being toggled via `classList.toggle`, not by reading/writing the
`display` property directly, so the CSS swap is transparent to the
existing logic.

## Verification
- Full test suite: 536/536 passing, unchanged (CSS-only change).
- Ran the packages-specific test files individually first for faster
  feedback: mobile filter, public listing, pagination, detail page —
  all passing.
