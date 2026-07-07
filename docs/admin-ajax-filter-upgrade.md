# Admin list pages: Apply-button → AJAX in-place filtering

## What happened
Four admin list pages (Packages, Continents, Countries, Users) still used
a traditional `<form method="GET">` with an "Apply" button for filtering.
Every filter change caused a full page reload. The other admin list pages
(Inquiries, Blog, Visa, Testimonials, Contact Messages) were already
upgraded to AJAX in-place filtering.

Also audited edit_blog.html — its back button was already correct (Preview
and Back are both below the h1 in a flex div), so no change was needed.

## Decision
Upgraded all four remaining pages to match the established AJAX pattern
used by Blog and Visa: wrap filterable content in a named app div, intercept
form submits and link clicks via JS, fetch the page, extract the app div
from the response, replace in place, push URL to browser history. Browser
back/forward works via popstate listener. No backend route changes needed.

## Changes (templates only — no route or model changes)
- `templates/admin/packages.html`
  - Removed "Apply" button from filter form.
  - Wrapped table-card + pagination + bulk-form in `<div id="pkgsApp">`.
  - Added AJAX IIFE to existing `<script>` block.
- `templates/admin/continents.html`
  - Removed "Apply" button.
  - Wrapped table-card in `<div id="continentsApp">`.
  - Added AJAX IIFE to existing `<script>` block.
- `templates/admin/countries.html`
  - Removed "Apply" button.
  - Wrapped table-card in `<div id="countriesApp">`.
  - Added AJAX IIFE to existing `<script>` block.
- `templates/admin/users.html`
  - Removed "Apply" button.
  - Wrapped table-card + pagination in `<div id="usersApp">`.
  - Added new `<script>` block with AJAX IIFE (page had no prior JS).

## Result
Full suite: 485 passed (no change — all template changes, no backend logic).
