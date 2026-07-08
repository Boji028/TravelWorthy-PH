# Add mobile off-canvas drawer for the admin sidebar

## Problem
`templates/admin/base_admin.html` (the shared layout wrapping every
admin page) used a fixed `grid-template-columns: 240px 1fr` for the
sidebar and main content, with zero responsive treatment anywhere in
the file. Computed the actual impact: at a 375px phone, the sidebar's
fixed 240px left only **135px** for all page content - tables, forms,
the dashboard stats, everything, on every single admin page
(Dashboard, Packages, Users, Inquiries, Messages, Stories, Visa,
Reviews, Site Settings, Agents).

## Fix
Added a real off-canvas drawer pattern, scoped to phones only
(`@media (max-width: 768px)`) - tablets keep the existing two-column
layout, since a fixed 240px sidebar still leaves a workable ~580px
for content at iPad Air's 820px.

**CSS**: `.admin-layout` drops to a single column on phones.
`.admin-sidebar` becomes `position: fixed`, off-screen by default
(`transform: translateX(-100%)`), sliding in with `.admin-sidebar-open`.
A new `.admin-sidebar-backdrop` overlay dims the page behind the open
drawer and closes it on tap. A new `.admin-mobile-toggle` button
("Admin menu") sits in a sticky bar at the top of the content area,
visible only on phones.

**HTML**: added the toggle button and backdrop div inside
`.admin-layout`, and an `id="adminSidebar"` on the existing `<aside>`
for the JS to target. Nothing else in the sidebar or any individual
admin page template needed to change.

**JS**: added to the existing script block (same one that already
runs the custom confirm-modal logic). Toggle button opens/closes the
drawer; tapping the backdrop, pressing Escape, or tapping any sidebar
link all close it - the "close on link tap" avoids the drawer/backdrop
staying visibly open during the brief moment before a full-page
navigation completes.

Because this all lives in the shared `base_admin.html` layout rather
than any individual page, every admin page gets the fix at once with
no per-page changes needed.

## Verification
- Parsed the entire `{% block content %}` region with Python's
  `html.parser`: zero errors, empty tag stack, 14/14 `<div>` and 1/1
  `<aside>` matched.
- Brace and paren balance check on the whole file: 120/120 braces,
  123/123 parens.
- Rendered four different admin pages (`/admin/`, `/admin/packages`,
  `/admin/users`, `/admin/continents`) through an actual Flask test
  client, logged in as admin: all 200 OK, all four confirmed to
  contain the new toggle button, backdrop, and sidebar id - proving
  the shared-layout fix actually reaches every page, not just the
  dashboard.
- Full test suite: 512/512 passing.

No migration needed - one shared template changed, no Python logic
touched.
