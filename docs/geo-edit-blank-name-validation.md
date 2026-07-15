# Validate blank name on continent/country edit

## Problem
`routes/admin.py`: `add_continent` and `add_country` both reject a
missing name, but `edit_continent` and `edit_country` assigned
`request.form.get("name", "").strip()` straight to the model. A blank
(or whitespace-only) name on edit saved an empty string — the column
is `nullable=False` but an empty string isn't NULL, so it committed
fine and left a nameless region/country in every dropdown and listing
that renders it.

## Fix
Both edit routes now validate the stripped name before touching the
model, mirroring their add counterparts: flash "name is required" and
redirect back to the edit form, leaving the record unchanged.

## Tests
`test_admin_geo_crud.py`: `test_blank_name_does_not_update` added to
both `TestEditContinent` and `TestEditCountry` — POST a whitespace-only
name, assert the original name survives.
