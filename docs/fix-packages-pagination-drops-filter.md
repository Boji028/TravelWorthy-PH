# Fix packages pagination dropping the active continent/country filter

## Problem
On `/packages`, filtering by continent (e.g. Oceania -> Australia) via the
toolbar correctly showed the filtered packages, but the pagination controls
below the grid still showed page numbers from the unfiltered "All" view.
Clicking "2" reverted to the default, unfiltered package list instead of
showing page 2 of the filtered results.

## Note on an earlier, incomplete attempt at this fix
An uncommitted local change already existed in this checkout (this file's
previous version, plus a partial edit to `list.html` and two tests in
`tests/test_packages_public.py`) that added `active_continent.id` /
`active_country.id` / etc. to the pagination `href`s. That part was correct
but incomplete: it only fixed how a *freshly server-rendered* page builds
its pagination links. It didn't touch the actual bug, which only shows up
after an AJAX filter action (see Root cause below), so it never caught the
real problem - its two tests both hit the route with a plain `client.get`,
which is a full server render and can't reproduce the AJAX-then-click
sequence that breaks in the browser. Both of those tests still pass under
the complete fix below; they're kept as-is.

## Root cause
The continent tabs, country dropdown links, and type-pill buttons on
`/packages` are all handled client-side via AJAX (`fetch` +
`history.pushState` in `list.html`'s inline script), which only ever
replaced the contents of `#packages-grid` (the cards). The pagination
`<div>` below it was a sibling that AJAX filtering never touched, so after
filtering it kept:
- its original `href` values, built from whatever filter was active on the
  very first full page load (usually none), and
- its original click listener, since pagination links share the
  `.country-tab` class with the continent tabs, and `addEventListener` was
  only attached once, at page load, to whatever `.country-tab` elements
  existed in the DOM at that time.

So after filtering by Oceania, clicking "2" fired that *stale* listener,
which fetched page 2 of the *unfiltered* list and swapped it into the grid
- looking like the filter had been silently dropped.

## Fix
Pagination is now rebuilt as part of every AJAX response, scoped to
whatever filter is currently active, instead of being rendered once and
left stale:

- `templates/packages/_cards.html` (new): the card-loop + empty-state
  markup, split out of the old `list_ajax.html` unchanged.
- `templates/packages/_pagination.html` (new): the Prev/page-number/Next
  markup, parameterized by `pagination`, `continent_id`, `country_id`,
  `destination`, `package_type` so it can be rendered from either the full
  page or the AJAX response with the correct filter baked into every link.
- `templates/packages/list_ajax.html`: now wraps `_cards.html` and
  `_pagination.html` in `#ajax-cards` / `#ajax-pagination` containers so the
  two pieces can be told apart after a fetch.
- `templates/packages/list.html`: the grid include now points at
  `_cards.html`; a new `#packages-pagination` div (sibling of
  `#packages-grid`) renders `_pagination.html`. A new `applyAjaxResponse()`
  JS helper splits every fetch response into its cards/pagination halves
  and updates both containers, replacing the 4 places that previously did
  `grid.innerHTML = html` directly. The 4 fetch `.catch()` blocks also clear
  `#packages-pagination` so a stale page list can't linger under an error
  message.
- `routes/packages.py`: the `XMLHttpRequest` branch now also passes
  `pagination`, `continent_id`, `country_id`, `destination`, `package_type`
  to `list_ajax.html`, matching what the full-page branch already had
  available via `active_continent` / `active_country`.

Net effect: if a filtered result set fits on one page (<= 9, e.g. the 6
Oceania packages in the report), no pagination renders at all. If it spans
multiple pages, every Prev/page-number/Next link carries the active
continent_id/country_id/destination/package_type forward, and clicking one
does a plain full-page navigation straight to the correct filtered page
(no stale AJAX listener involved, since the links are freshly inserted
each time).

## Follow-up: pagination was still causing a full page reload
After applying the fix above, clicking Prev/page-number/Next still caused
a full browser navigation (page flash/reload) instead of the smooth AJAX
swap used everywhere else on this page - on both desktop and mobile, since
they share the same markup and JS.

Cause: pagination links share the `.country-tab` CSS class with the
continent tabs, and the *original* click-binding loop
(`document.querySelectorAll('.country-tab').forEach(tab => tab.addEventListener(...))`)
only attaches listeners once, at page load, to whatever elements exist in
the DOM at that moment. Any pagination link inserted later - which is all
of them, since `applyAjaxResponse()` replaces `#packages-pagination`'s
contents on every filter action - never got a listener, so clicking it
fell through to the browser's default anchor behavior: a real navigation.

Fix: pagination now has its own delegated click handler, bound once to
`#packages-pagination` itself (the container element, which is never
replaced - only its children are). Delegation means it keeps working no
matter how many times the pagination links inside it get rebuilt. The
original continent-tab loop now explicitly skips anything inside
`#packages-pagination` so the two handlers can't both fire on the same
click. Pagination clicks also scroll the results section back into view,
since a real page navigation would have jumped to the top and a silent
AJAX swap otherwise wouldn't.

This is a client-side/JS-only fix - no route or test changes, so the
Python suite count is unchanged at 518/518. Verified by reading through
the event flow by hand (brace/paren balance and `node --check` on the
extracted script block both clean); this project has no browser-level JS
test coverage yet, same as the rest of the site's existing interactions.

## Verification
- New `tests/test_packages_pagination.py` (4 tests):
  - filtered result <= 9 items -> no pagination markup in the AJAX response
  - filtered result > 9 items -> AJAX pagination links carry `continent_id`
  - following a filtered `page=2` link returns only that continent's
    packages, not the unfiltered list
  - the full (non-AJAX) page render's pagination also carries the filter
- Existing `TestPaginationPreservesFilters` (2 tests, from the earlier
  attempt): still passing.
- Full suite: 518/518 passing (512 existing + 4 new + 2 from the earlier
  attempt).
- No migration needed -- template/JS restructuring plus one route change.
