# Custom-styled dropdowns for visa/packages mobile filters, plus a bug fix

## Bug fix first
The mobile region dropdown on the visa page was showing at the same
time as the desktop pill row instead of replacing it — both visible
at once, redundant. Cause: `.visa-region-filter-row`'s div has an
inline `style="display:flex;..."`, and inline styles always beat a
plain class rule regardless of specificity or media query, so
`.visa-region-filter-row { display: none; }` inside the `@media
(max-width: 768px)` block never actually took effect. Needed
`!important` to win — the same trick this file already used
elsewhere (`flex-wrap: nowrap !important`) for this exact situation
(overriding an inline style at a breakpoint). Checked the packages
page for the same risk; its dropdowns don't have a conflicting inline
`display`, so no equivalent issue there.

## Custom dropdown component
Native `<select>` elements can only be styled up to their closed box —
the open option list is rendered by the OS/browser and isn't reachable
with CSS on most platforms, which is what made the previous dropdowns
look plain despite the `.form-control` styling on the closed state.
Built a reusable custom dropdown instead, used in three places: the
visa region filter, and both the continent and country pickers on the
packages mobile sheet.

**`static/css/main.css`** — new `.cselect*` rules, added right after
`.form-control` since it's a themed alternative to the same kind of
control:
- `.cselect-trigger` — the closed box, same visual language as
  `.form-control` (border, radius, focus-teal on open) plus a chevron
  that rotates 180° when open.
- `.cselect-list` — the open panel: teal border, `max-height`/`opacity`
  transition (not `display`, so it can animate), scrolls internally
  past 280px so a long list doesn't blow out the sheet.
- `.cselect-option` / `.selected` — hover tint, and a teal-tinted
  background + checkmark icon for the selected row.
- `.cselect-disabled` — dims and disables the trigger (used for the
  country dropdown before a continent is picked).

**`static/js/main.js`** — new `initCustomSelect(root, onChange)`,
shared by all three instances rather than writing three copies:
- Click the trigger to toggle `.open` on the root; click anywhere
  outside closes it; Enter/Space toggles, Escape closes.
- Clicking an option updates `.selected` + the checkmark, updates the
  trigger's visible label, closes the panel, and fires `onChange(value,
  label)`.
- Returns `{ setOptions(options, selectedValue), getValue(),
  setDisabled(bool) }` — `setOptions` fully rebuilds the option list,
  which is what the country dropdown needs every time the continent
  changes.

## Wiring per page
**`packages/visa.html`** — swapped the native `<select>` for `.cselect`
markup with the same region list rendered as `.cselect-option` divs.
`filterVisa(region, btn)`'s `btn` param was already optional from the
prior dropdown pass; the `.cselect` just calls `filterVisa(value)` from
its `onChange` callback the same way the old `<select onchange=...>`
did.

**`packages/list.html`** — both selects became `.cselect` instances.
`populateCountrySelect()` now calls `countrySelect.setOptions(...)`
instead of manually rebuilding `<option>` elements, and
`countrySelect.setDisabled(!continentId)` instead of the native
`.disabled` property. Apply-time reads switched from `.value` /
`.selectedOptions[0]` to `.getValue()` and the trigger's `.cselect-label`
text. The Clear button's continent reset manually toggles `.selected`
+ the checkmark back to "All continents" by index, since the continent
list is static server-rendered markup rather than a JS array (unlike
country options, which already come from the `continentCountries` data
structure and go through `setOptions`).

`continentCountries` — no changes; still the same embedded JS object
from the previous pass, just now feeding `.setOptions()` instead of
manually-created `<option>` elements.

## Tests
`tests/test_packages_mobile_filter.py` updated again — element ids
(`mobileContinentCSelect`/`mobileCountryCSelect`), the `data-value`
attribute instead of `value`, and the `populateCountrySelect(...)` JS
call now reads `continentSelect.getValue()` instead of
`continentSelect.value`.

## Verification
- Full suite: 537/537 passing, unchanged count (tests updated
  in-place, no tests added or removed this round).
- `node -c` on `main.js`: valid syntax.
- `main.css` brace balance: 161/161.
- Flask test-client render check: confirmed the selected continent
  option carries `selected` + the checkmark icon and the unselected
  "All continents" option carries neither; confirmed
  `.visa-region-filter-row { display: none !important; }` is present
  in the rendered page.

## Second bug found after delivery: dropdowns didn't appear at all
After the first delivery, the custom dropdowns didn't render/respond
on either page — worse than "plain," now nonfunctional. Cause: script
load order. `base.html` loads `main.js` (which defines
`initCustomSelect`) *after* `{% block content %}` closes:
```
{% block content %}{% endblock %}   <!-- line 208 -->
...
<script src=".../main.js"></script>  <!-- line 257 -->
```
Both pages' own inline `<script>` blocks live inside that content
block, and both called `initCustomSelect(...)` immediately at parse
time — before the browser had even reached, let alone executed,
`main.js`'s `<script src>` tag further down the page. That throws a
`ReferenceError: initCustomSelect is not defined`, which halts the
rest of that script block silently (no visible error in the UI, just
inert buttons).

Fix: wrapped the `initCustomSelect(...)` call sites in
`document.addEventListener('DOMContentLoaded', function () { ... })`
instead of calling them immediately:
- `visa.html`: just the few lines that call `initCustomSelect` for the
  region dropdown.
- `list.html`: the whole "Mobile filter sheet" block, converting it
  from an immediately-invoked `(function () { ... })()` to
  `document.addEventListener('DOMContentLoaded', function () { ... })`
  — same closure/scoping, just deferred. `openPdfViewer` and other
  functions used by inline `onclick` attributes elsewhere on the page
  were deliberately kept *outside* this wrapper (they need to stay in
  global scope to be reachable from `onclick="..."`).

`DOMContentLoaded` fires only once the entire document — including
`main.js`'s later `<script>` tag — has finished parsing and executing,
regardless of where in the document the listener itself was
registered, so this reliably resolves the ordering problem without
needing to move `main.js`'s own position (which risked breaking the
nav-toggle code that already runs correctly today because it executes
after the nav HTML it targets already exists in the DOM).

Re-verified: full suite still 537/537, and a render check confirms
both `document.addEventListener('DOMContentLoaded', ...)` wrappers are
present in the served HTML in place of the old immediate calls.
