# Replace mobile filter chips with dropdowns on visa and packages

## What changed
Both public pages' mobile filter now use native `<select>` dropdowns
instead of tappable pill/chip rows, at the existing 768px breakpoint.
Desktop is untouched on both pages.

**`packages/visa.html`** — the region pill row (`.visa-region-filter-row`)
stays for desktop; added a parallel `<select class="visa-region-filter-select">`
that's shown only under 768px (CSS visibility swap, not a markup swap —
both exist in the DOM, only one is visible at a time). `filterVisa(region,
btn)`'s `btn` param is now optional so the dropdown's `onchange="filterVisa(this.value)"`
works without a button to mark `.active` — pill clicks still pass `this`
and get the active-state toggle as before.

**`packages/list.html`** — bigger change, since this page has two
filter dimensions (continent, then country) where visa only has one
(region). The old mobile sheet had a horizontally-scrolling continent
chip row, and one `.mobile-country-grid` panel per continent
pre-rendered server-side, toggled open/closed client-side by
`display`/class. Replaced with two cascading `<select>` elements:
picking a continent repopulates the country dropdown from a
`continentCountries` JS object (also embedded server-side, one entry
per continent → array of `{id, label}` for its active countries).
Picking "All continents" clears and disables the country dropdown,
since there's nothing to cascade from.

Rewrote the `Continent.countries` loop to filter with
`| selectattr('is_active') | list` before iterating, specifically so
`loop.last` (used to decide whether to emit a trailing comma in the
generated JS array) refers to the last *visible* country, not the last
country before the `{% if country.is_active %}` filter was applied —
the original per-continent-panel loop had this same filter but never
needed comma-correctness since it was rendering HTML buttons, not a JS
array literal. Verified with a script producing multiple edge cases
(a continent with an inactive country in the middle of the list, and a
continent with zero active countries) — output is valid JS in both
cases, no dangling commas, empty continents get `[]`.

Removed the now-unused `.mobile-region-chips` / `.mobile-chip` /
`.mobile-country-grid` / `.mobile-country-chip` CSS (the animation
transitions added on these in the previous session are gone along with
them — dropdowns don't need a chip-style hover/active fade).

The actual AJAX fetch-and-swap on Apply is untouched — same
`fetchPackages()` / `applyAjaxResponse()` / skeleton-loading flow as
before, just reading `continentId`/`countryId` off the two selects
instead of off `.active` chip elements.

## Why dropdowns specifically here
Per the conversation: visa's region filter only has 6 options, where
pills were arguably better (see the earlier chip-row work). Packages'
filter has two levels — continent, then country within it — and once
there's a second cascading dimension, a dropdown reads more
predictably than a chip-row-that-reveals-a-grid pattern, and keeps
both pages using the same interaction model end to end for consistency
rather than mixing dropdown-for-one-level and chips-for-another.

## Tests
`tests/test_packages_mobile_filter.py` rewritten — the old tests
asserted on chip markup and `data-continent-panel` attributes that no
longer exist. New tests check: the two select elements render, the
active continent's `<option>` carries `selected`, the active country's
id is threaded into the client-side `populateCountrySelect()` call
that runs on page load (can't assert the country `<option selected>`
directly since that dropdown is populated by JS at runtime, not
server-rendered), every continent gets an entry in `continentCountries`
regardless of which one is active, and inactive countries are excluded
from that data entirely.

## Verification
- Full suite: 537/537 passing (536 + 1 net-new test).
- Flask test-client smoke check hitting both pages with edge-case data
  (a continent with an inactive country skipped mid-list, a continent
  with zero active countries) — both render 200, generated JS is
  syntactically valid in both cases.
