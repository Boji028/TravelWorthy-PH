# Fix admin inquiries table missing overflow-x above mobile width

## What was wrong
`templates/admin/inquiries.html`'s `.inquiries-table-wrap { overflow-x:
auto; }` rule only existed inside `@media (max-width: 768px)`. Above that
width the wrapper had the browser default `overflow: visible`, so a long
customer email in `.cust-email` had no scroll or wrap safety net on
tablet/desktop widths — it could overflow the card instead of scrolling.
`admin/users.html` (inline `style="overflow-x:auto"`, unconditional) shows
the correct pattern this page was missing.

## Fix
Moved `.inquiries-table-wrap { overflow-x: auto; }` out of the
`@media (max-width: 768px)` block into the page's base `<style>` rules, so
it applies at every viewport width, not just mobile.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding F2).

## Tests
None added — this is layout/overflow behavior, not something the existing
Python/Jinja test suite can assert on (no rendered-CSS testing in this
project). Ran `tests/test_admin_inquiries.py` (18 tests) to confirm the
template still renders correctly; all pass. **Manual re-check requested:**
please view the admin Inquiries list at desktop and tablet widths (e.g.
1024px and 1280px) with a long customer email in the list and confirm it
scrolls horizontally within the table instead of overflowing the card.
