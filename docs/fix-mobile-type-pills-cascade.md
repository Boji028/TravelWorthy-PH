# Fix type-pills not collapsing in mobile packages toolbar

## Problem
On the packages list page at phone widths (tested at Samsung Galaxy
S8+, 360px), the "All types / Domestic / International" filter pills
showed permanently above the collapsed toolbar, instead of staying
hidden until "Filters" is tapped - producing an extra, redundant row
above the search bar.

## Root cause
`templates/packages/list.html` has three CSS rules touching
`.type-pills`:

1. Inside `@media (max-width: 768px)`, a "collapsed by default" group
   sets `display: none` on `.type-pills` along with several sibling
   elements (`.country-tabs-inner`, `.filter-label`, `#btn-apply`,
   `#btn-clear`, `.active-filter-pill`).
2. Inside the same media query, `.toolbar.filters-open .type-pills`
   sets `display: flex` when the mobile filter panel is expanded.
3. Outside any media query, much further down the file, a base rule
   sets `.type-pills { display: flex; gap: .4rem; }` for desktop.

Rule 1 and rule 3 both target the bare `.type-pills` selector with
identical specificity (one class each). CSS resolves ties between
equal-specificity rules by source order - later wins - and rule 3
appears later in the file than rule 1, so it silently overrode the
mobile hide rule at every viewport width, media query or not.

None of the other elements in that "collapsed by default" group had
this problem, because their own base rules all happen to sit earlier
in the file than the media query block, so the media query's later
`display: none` correctly won for them without any specificity games
needed.

## Fix
Changed the mobile hide-rule's selector from the bare `.type-pills`
to `.filter-inner .type-pills` (its actual parent in the markup),
which has higher specificity (two classes) than the base rule (one
class) and therefore wins regardless of where either rule sits in the
file - no code needed to move, no `!important` needed.

Verified this doesn't disturb the "expanded" state:
`.toolbar.filters-open .type-pills` (three classes worth of
specificity) already outranks both the base rule and the new
two-class collapsed rule, so tapping "Filters" still correctly shows
the pills.

## Verification
- Traced every rule touching `.type-pills` (exactly three, confirmed
  by search) and checked specificity by hand for all three states:
  mobile collapsed, mobile expanded, desktop - each resolves to the
  intended `display` value.
- Brace-balance check on the edited file: 302/302 matched.
- Full test suite: 512/512 passing (pure CSS selector change, no
  Python or template logic touched).

No migration needed - stylesheet-only change within one template.
