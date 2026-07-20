# Add mobile breakpoints to admin form grids

## What was wrong
Several admin add/edit form pages laid out fields in a CSS grid with no
`@media` query to stack them on phone-width screens, unlike the
public-facing equivalents (`bookings/plan_my_trip.html`,
`bookings/inquire_package.html`), which both correctly stack `.form-row`
to one column at `<=768px`:

- `templates/admin/add_package.html` / `edit_package.html` — `.form-row`
  (name/duration fields etc.) had zero `@media` queries in either file,
  plus a second, separate inline `display:grid;grid-template-columns:1fr
  1fr` for the latitude/longitude fields with the same gap.
- `templates/admin/add_visa.html` / `edit_visa.html` — three inline grids
  (`1fr auto` for country name/flag, `1fr 1fr` for region/visa type,
  `1fr 1fr 1fr` for processing time/stay validity/document count), none
  wrapped in any class, so no media query could target them at all.
- `templates/admin/edit_country.html` — one inline grid (`1fr auto` for
  country name/flag) with a `class="form-row"` attribute that was never
  backed by an actual `.form-row` CSS rule, so it did nothing; the layout
  came entirely from the inline style, which a media query can't override
  without `!important` since inline styles win over any stylesheet rule.

`templates/admin/add_country.html` was also flagged in the original audit
finding, but on inspection it turned out to have no grid layout at all —
every field is already single-column. Left untouched (false positive).

## Fix
- `add_package.html` / `edit_package.html`: added the standard
  `@media (max-width: 768px) { .form-row { grid-template-columns: 1fr;
  gap: 0; } }` rule (matching the public booking forms), and converted
  the separate inline latitude/longitude grid to reuse the same
  `.form-row` class instead of duplicating the pattern.
- `add_visa.html` / `edit_visa.html`: introduced three classes
  (`.visa-row-name`, `.visa-row-2`, `.visa-row-3`) for the three column
  counts used on these pages, moved the `display`/`grid-template-columns`/
  `gap` declarations out of inline styles and into these classes, and
  added the same 768px stacking media query. Non-layout inline styles
  (`align-items:end`, `margin-bottom:1rem`) were left inline since they
  don't need to change at mobile width.
- `edit_country.html`: added an actual `.form-row` CSS rule (base +
  768px override) and removed the redundant inline style that was
  overriding it, since the element already had the class attribute.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding
F4). The two extra inline grids in add/edit_package.html (latitude/
longitude) weren't in the original finding — found while implementing
the fix, by grepping each file for every remaining `display:grid`/
`grid-template-columns` occurrence rather than stopping at the one the
audit named.

## Tests
None added — this is layout/breakpoint behavior the Python/Jinja test
suite can't assert on (no rendered-CSS testing in this project). Ran the
full admin package/visa/geo test suites (106 tests across
`test_admin_package_crud.py`, `test_admin_packages.py`,
`test_admin_visa.py`, `test_admin_geo.py`, `test_admin_geo_crud.py`) to
confirm all six templates still render and submit correctly; all pass.

**Manual re-check requested** (I can't visually verify rendering myself):
please view each of the six edited admin forms (Add/Edit Package, Add/Edit
Visa, Edit Country) at a phone width (~375px) and confirm the two-and
three-column rows stack to one column instead of squeezing side by side.
