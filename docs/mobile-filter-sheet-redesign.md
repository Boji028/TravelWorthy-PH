# Redesign the mobile packages filter as a bottom sheet

## Problem
On mobile, tapping "Filters" on the Packages page expanded the same
desktop toolbar elements inline, pushing page content down. This looked
cluttered: region pills wrapped across uneven rows, and tapping a
continent revealed its countries as a plain stacked text list inline,
pushing everything below it further down the page.

## Approved direction
A preview was built and approved before any code changed (per usual
workflow): replace the inline-expanding panel with a slide-up bottom
sheet, matching the collapsed search + "Filters" trigger already in
place. Inside the sheet: destination search, a type segmented control,
a single scrollable row of region chips, and a 2-column country chip
grid under whichever region is selected. Clear / Apply are pinned at the
bottom of the sheet.

## Implementation
Desktop is untouched — same toolbar, same continent-dropdown hover
menus, same AJAX wiring as before. Everything here is scoped to mobile
(`templates/packages/list.html`, `@media (max-width: 768px)`) and adds a
separate, self-contained set of elements rather than trying to reuse the
desktop markup across two very different layouts:

- New markup: `#mobileSheetOverlay` > `.mobile-sheet` (handle, header with
  close button, body, footer). The body renders a destination input, a
  type segmented control (`.mobile-seg`), a region chip row
  (`.mobile-chip`, one per continent plus "All"), and one
  `.mobile-country-grid` panel per continent (all rendered up front, only
  the active one shown) so switching regions in the sheet doesn't need a
  server round trip.
- New CSS: the old `.toolbar.filters-open ...` inline-expand rules and
  the touch-tap continent-dropdown rules are removed (dead once
  `.country-tabs-inner` is mobile-hidden) and replaced with the sheet's
  own rules, using `position: fixed` for the overlay (safe here — this is
  a real page, not a sandboxed widget) and a small slide-up keyframe.
- New JS (bottom of the script, after `grid`/`applyAjaxResponse`/etc. are
  already defined): a self-contained IIFE tracking `mobileContinentId` /
  `mobileCountryId` / `mobilePackageType` as the user taps around the
  sheet (staged, not applied yet), then on "Apply filters" builds the
  query string and does the same AJAX fetch + `applyAjaxResponse()` swap
  the rest of the page already uses, closes the sheet, and syncs the
  desktop toolbar's own state variables (`activeCountryId`,
  `activeDestination`, `activePackageType`, the search input, the
  breadcrumb pill) in case the viewport is later resized to desktop
  without a reload.
- The old `#mobileFilterToggle` click handler (which used to toggle a
  `filters-open` class and swap its own label between "Filters"/"Close")
  now just opens the sheet; the sheet has its own close button and
  backdrop-tap-to-close instead.

## Verification
- New `tests/test_packages_mobile_filter.py` (4 tests): sheet markup
  renders with the default "All" chip active when no filter is set,
  active continent/country are marked `active` with the right
  `data-label`, every continent gets its own country panel (not just the
  active one), and the type segment reflects `package_type` from the
  query string.
- Manually rendered the sheet HTML with seeded Oceania/Australia data and
  confirmed by hand: correct `active` classes, matching
  `data-continent-panel` / `data-continent-id`, correct `data-label`
  breadcrumb text.
- Brace/paren balance and `node --check` on the extracted script block
  both clean.
- Full suite: 522/522 passing (518 existing + 4 new). Desktop's own
  tests (`test_packages_public.py`, `test_packages_pagination.py`) are
  untouched and still pass, since desktop markup wasn't changed.

No migration needed — template/CSS/JS only.
