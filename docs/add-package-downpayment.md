# Package downpayment field and bulk Downpayments page

**Date:** 2026-09-26

## What changed

Admin can now enter an optional downpayment per package, as free text
(e.g. "30% of package price" or "PHP 5,000 per pax, non-refundable").
Leaving it empty hides it.

- `models/package.py`: new nullable `downpayment` column, `String(200)`.
- `migrations/versions/c6d2a8e4f193_add_package_downpayment.py`: adds the
  column (revises `a3c9e5f17b42`).
- `routes/admin.py`: add and edit package save the trimmed value (empty
  saved as None, capped at 200 characters). New `package_downpayments`
  route at `/admin/packages/downpayments` lists every package with its
  own downpayment box and saves them all in one POST; only packages whose
  value changed are updated.
- `templates/admin/package_downpayments.html`: new page. Search box,
  "only packages without a downpayment" filter, checkboxes with an
  "Apply to selected" bar that fills the ticked rows, changed boxes
  highlighted with an unsaved-changes count, one Save all button, and a
  leave-page warning when there are unsaved changes.
- `templates/admin/packages.html`: "Downpayments" button next to Add
  Package.
- `templates/admin/add_package.html`, `edit_package.html`: new
  "Downpayment" text field under the price; included in the Add Package
  autosave draft.
- `templates/packages/detail.html`: "Downpayment" row in the price box
  under "Price per person". On price-on-request packages it shows under
  the request note instead. Long text wraps on the right.
- `tests/test_admin_package_crud.py`: 13 new tests for the field, the
  public row and the bulk page.

## Deploy

Needs `flask db upgrade` on Render after pushing.
