# Fix About page mobile grid gaps

## Problem
The About page's grids were only ever given a tablet-tier reduction
(most at `1024px`, from the earlier breakpoint consolidation pass),
with nothing further for actual phone widths. Three specifically
looked broken or cramped on a 375px screen:

- `.about-values` (Mission / Vision / Tagline cards): had **zero**
  responsive treatment at all - still a rigid 3-column grid at any
  width, each column ~87px wide on a phone with full paragraph text
  inside.
- `.service-list`: reduced from 3 to 2 columns at `1024px`, but
  several items have long text ("Documents assistance (PSA,
  apostille)", "Team building & recognition trips") that wraps badly
  in a ~155px column.
- `.dest-grid` (destination photo tiles): reduced from 8 to 4 columns
  at `1024px`, but 4 square tiles plus gaps in ~311px leaves each
  tile only ~70px - too small for the image and its label overlay to
  read.

## Not changed
`.why-grid` and `.logo-grid` also only reduce to 2 columns with no
further phone-tier step, but their content (short card text, small
logo images) holds up fine at that width, and it's the same pattern
already in use on `home.html`'s equivalent `.tw-why-grid` - left
alone for consistency rather than fixing one instance of a pattern
used elsewhere.

## Fix
`templates/main/about.html` - added a `@media (max-width: 768px)`
step for each of the three, placed next to their existing rules:

- `.about-values`: `repeat(3, 1fr)` -> `1fr` (stacks to one column)
- `.service-list`: `repeat(2, 1fr)` -> `1fr` (stacks to one column)
- `.dest-grid`: `repeat(4, 1fr)` -> `repeat(2, 1fr)`

Tablet (769-1024px) and desktop (>1024px) are unchanged.

## Verification
- Brace-balance check on the edited file: 206/206 matched.
- Confirmed all 7 media queries now present (4 existing `1024px`
  tablet-tier + 3 new `768px` phone-tier).
- Full test suite: 512/512 passing (pure CSS additions, no Python or
  template logic touched).

No migration needed - stylesheet-only change within one template.
