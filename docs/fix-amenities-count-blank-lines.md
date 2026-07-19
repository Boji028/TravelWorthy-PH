# Fix "Show all N amenities" counting blank lines

**Date:** 2026-07-19

## Root cause

```jinja
{% set amenity_list = package.amenities.split('\n') | selectattr('strip') | list %}
```

`selectattr('strip')` tests whether each item's `.strip` **attribute**
is truthy - but `.strip` without `()` is the bound method object
itself, not the result of calling it. A bound method is always
truthy, so this never actually filtered anything out. Every line from
`.split('\n')`, blank ones included, stayed in `amenity_list`, and the
button's `{{ amenity_list|length }}` counted them all.

The rendering loops had their own separate `{% if item.strip() %}`
guard that correctly skipped blank lines when displaying items - so
blank amenities never showed up as empty boxes, but they still
inflated the count. That mismatch is exactly what got reported: 4
amenities visible, "Show all 11" on the button, only 2 more real ones
actually behind it (6 real + 5 blank = 11 raw lines).

## Fix

```jinja
{% set amenity_list = package.amenities.split('\n') | map('trim') | select | list %}
```

`map('trim')` strips whitespace from every line first; `select` with
no test name filters by truthiness, dropping anything that trimmed
down to an empty string. `amenity_list` now only ever contains real,
already-trimmed amenities, so the count is always accurate. Removed
the now-redundant `{% if item.strip() %}` / `item.strip()` calls in
both rendering loops - the list is guaranteed clean going in.

Checked for the same `selectattr('strip')` pattern elsewhere in the
codebase - this was the only occurrence. Inclusions/exclusions use a
different pattern (inline `{% if item.strip() %}` per loop, no
separate count shown anywhere), so they were never affected by this
particular bug.

## Tests

Added to `tests/test_packages_detail.py`:
- `test_amenities_count_excludes_blank_lines` - 6 real amenities +
  5 blank lines (matching the reported 11-total case). Since 6 fits
  within the first-8 display, the fix means no "Show all" button
  should appear at all anymore.
- `test_amenities_show_all_count_is_accurate_with_blank_lines` - 10
  real amenities + 12 blank lines (22 raw lines total). Asserts the
  button shows "Show all 10", never the inflated raw count.

Full suite: 559 passed (557 previous + 2 new), 2 pre-existing warnings
unrelated to this change.
