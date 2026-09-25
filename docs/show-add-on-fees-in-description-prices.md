# Show add-on fees and full date ranges in description prices

**Date:** 2026-09-25

## Problem

Travel date lines in a package description such as
`Oct 26 – Nov 5 (+USD 100)` were shown on the detail page as a card
reading "Oct 26" and "USD 100". Two bugs in `description_format.py`:

- The price pattern matched only `USD 100`, so the `+` was dropped and
  the extra fee looked like the full price.
- The dash in a date range was treated as the "label — price" separator
  (meant for lines like `Belmont Hotel — ₱6,999`), so only the start
  date was kept and the end date disappeared.

## What changed

- `description_format.py`: `_parse_price()` now detects a `+` right
  before the price and keeps it (`+USD 100`), marked as an add-on. The
  dash split only applies when the price starts the right-hand side,
  otherwise the whole line minus the price is used as the label, with
  leftover empty brackets removed. New `_price_unit()` adds an
  "additional fee" note (plus "per person" when present).
- `templates/packages/detail.html`: on screens up to 768px, the note in a
  single price row stacks under the amount so the date label isn't
  squeezed.
- `tests/test_description_format.py`: 5 new tests covering the plus
  sign, the fee note, full date-range labels, bracket cleanup, and that
  normal prices are unaffected.

No migration. Admin keeps writing descriptions the same way.
