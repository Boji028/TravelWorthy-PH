# Packages mobile toolbar: Clear button and breadcrumb pill escaped the media-query hide

## What was wrong
Same inline-style vs media-query bug class fixed twice before, this time
in the packages list mobile toolbar. The `@media (max-width: 768px)` block
in `templates/packages/list.html` hides the desktop-only filter controls
with plain `display: none`, but two of the listed selectors lose that
fight:

- `#btn-clear` gets `style="display:inline-flex"` inline - server-side
  when the page loads with `?destination=...`, and from JS whenever a
  destination filter is applied (including from the mobile sheet itself,
  whose apply handler syncs `btnClear.style.display`). Inline style beats
  any non-`!important` rule, so the desktop Clear button reappeared in
  the mobile toolbar after filtering.
- `.active-filter-pill` is shown via `.active-filter-pill.visible`
  (specificity 0,2,0), which outranks the media query's bare
  `.active-filter-pill` (0,1,0). With any continent/country filter
  active, the desktop breadcrumb pill rendered on mobile despite the
  comment saying these controls live inside the filter sheet there.

## Fix
Added `!important` to the media query's `display: none` group - the same
pattern the visa page already uses for `.visa-card` in its
reduced-motion block - and a comment explaining why it is needed.

## How it was found
Re-sweep of the two bug classes from the previous pass, requested before
deploy: cross-checked every selector inside template media queries
against inline `display`/`opacity` styles and higher-specificity show
rules on the same elements.
