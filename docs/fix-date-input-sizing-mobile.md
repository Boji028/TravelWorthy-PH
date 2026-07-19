# Fix oversized date input fields on mobile (iOS Safari)

**Date:** 2026-07-19

## Root cause

`.form-control` uses the site's decorative display font
(`font-family: 'Pogonia', sans-serif`) for every form input across the
site. That's fine for regular text inputs, which CSS fully controls -
but `input[type="date"]` is a native, OS-rendered widget that CSS can
only partially restyle. iOS Safari specifically uses the input's font
metrics to size its internal segmented date-picker control, so an
unusual display font inflated the whole input to a much taller box
than a normal field - exactly the oversized, awkward-looking "From"
and "To" fields reported, which then made the whole form read as
badly/inconsistently spaced even though the actual `.form-group`
margins were untouched and fine.

The two-column "From"/"To" row already collapses to a single column
correctly at ≤768px (`templates/packages/detail.html`'s
`.form-row` media query) - that part was never broken.

## Fix

Added a targeted override in `static/css/main.css`, right after
`.form-control`:

```css
input[type="date"].form-control,
input[type="time"].form-control,
input[type="datetime-local"].form-control {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: normal;
}
```

Resets just these input types back to the system font stack the
native control actually expects, without touching the display font
anywhere else. Fixed globally in `main.css` (not just the inquire
modal's local styles) since `.form-control` + `type="date"` is the
same pattern used on Plan My Trip and anywhere else a date field
appears - one fix, applies everywhere automatically.

## Tests

CSS-only change to a shared stylesheet. Ran
`test_packages_detail.py` and `test_bookings.py` (44 tests, both
inquiry entry points that use date fields) plus the full suite as a
broader sanity check since `main.css` is loaded site-wide. Full suite:
559 passed, 2 pre-existing warnings unrelated to this change.
