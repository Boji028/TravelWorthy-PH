# Fix content overflow across 5 admin pages on mobile

## Context
With the sidebar drawer now working, these screenshots showed a
different layer of the same underlying problem: the *content* inside
several admin pages was never given any mobile treatment, so tables
and grids overflow the viewport once the sidebar isn't eating most of
the width anymore.

## 1. Dashboard stat cards - grid blowout
`templates/admin/dashboard.html`

`.stats-grid` already had media queries reducing
`repeat(5, 1fr)` -> `repeat(3, 1fr)` at 1024px -> `repeat(2, 1fr)` at
768px - correctly ordered, no cascade bug. But `1fr` grid tracks still
have `min-width: auto` by default, so a track won't shrink below its
content's natural minimum width. With icon + number + label inside
each `.stat-card`, the row was wide enough to blow out the container
instead of wrapping to 2 clean columns - which is exactly what showed
up as a partially cut-off third card in the screenshot.

Fix: `repeat(2, 1fr)` -> `repeat(2, minmax(0, 1fr))` at all three
breakpoints (and the 5- and 3-column desktop/tablet versions too, for
the same reason). `minmax(0, 1fr)` lets the track shrink to zero
before growing, so content inside is now forced to wrap within its
column instead of forcing the grid wider than the viewport.

## 2-5. Admin data tables - missing or broken scroll wrapper
Checked every page using `.admin-table` first, since it's shared
across 6 files: `continents.html`, `countries.html`, `packages.html`,
and `users.html` already wrap it in `<div style="overflow-x:auto">` -
those four needed no changes.

**`templates/admin/visa.html`** was the one exception - its table sits
inside a card `<div>` using `overflow: hidden` (for the card's rounded
corners), with no scrollable wrapper at all. `overflow: hidden`
actively clips overflowing content instead of allowing scroll, which
is exactly the cut-off table seen in the screenshot. Added an inner
`<div style="overflow-x:auto">` around just the `<table>`, so the
outer card keeps its rounded-corner clipping while the table itself
can scroll horizontally within it.

**`templates/admin/contact_messages.html`**, **`templates/admin/blog.html`**,
and **`templates/admin/agents.html`** had no wrapper at all around
their tables. Added a `.{page}-table-wrap { overflow-x: auto; }` class
to each (matching the existing pattern already used on
`admin/inquiries.html`) and wrapped each `<table>` in it.

## Verification
- Brace balance on all 5 edited files: all matched (dashboard 126/126,
  contact_messages 136/136, blog 147/147, visa 122/122, agents 78/78).
- `<div>`/`<table>` open/close tag counts matched on all 4 files with
  new wrapper divs added.
- Full test suite: 512/512 passing.
- Rendered all 5 pages through an actual Flask test client, logged in
  as admin: all 200 OK. Specifically confirmed the served HTML
  contains the new `overflow-x:auto` wrapper around the visa table
  (not just the pre-existing `admin-table` class, which would have
  been present either way) and the `minmax(0, 1fr)` grid fix on the
  dashboard.

No migration needed - template-only changes, no Python touched.
