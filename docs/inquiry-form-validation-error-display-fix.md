# Fix: inquiry forms silently re-render on validation failure

**Date:** 2026-07-17

## What was actually wrong

Reported as "I submitted a guest inquiry and after clicking send it just
shows up [the same page] again." Root cause: both
`templates/bookings/inquire_package.html` (package detail + the
standalone `/bookings/inquire/<id>` page) and
`templates/bookings/plan_my_trip.html` never read `form.<field>.errors`
anywhere. When `InquiryForm.validate_on_submit()` fails - wrong phone
format, a single-word name (`FullNameValidator` requires first + last),
a departure date that isn't strictly in the future, a return date
before the departure date, etc. - `routes/bookings.py` correctly
re-renders the same template with the invalid `form` object, but the
template threw every error away and showed a completely blank form.
From the visitor's side this looks exactly like nothing happened.

Existing tests (`test_missing_name_fails_validation`, etc.) only
checked that no `Inquiry` row got created - never that the response
actually told the user why, which is how this shipped unnoticed.

## Fix

Both templates now follow the same pattern already used in
`register.html` and `contact.html`:
- Every input gets `value="{{ form.field.data or ... }}"` so a failed
  submission doesn't wipe what the visitor typed.
- Every field gets `{% if form.field.errors %}` showing
  `form.field.errors[0]` right under the input, styled with the
  existing `var(--danger)` design token (no new CSS needed).
- The three pax fields (adults/children/infants) share one error line
  under the grid rather than three, to keep that row compact.

## Not touched (flagged, not fixed)

`plan_my_trip.html`'s "With/Without Airfare" toggle is a plain HTML
button pair with a hidden `with_airfare` input - it isn't a WTForms
field on `InquiryForm`, and `routes/bookings.py::plan_my_trip()` never
reads `request.form.get("with_airfare")` at all. The customer is forced
to pick one before the JS lets them submit, but the choice is discarded
- never saved on `Inquiry`, never visible to admin. Separate bug from
what was reported here; needs a model column + migration, so left as a
follow-up rather than folded into this fix.

## Tests

Added to `tests/test_bookings.py`:
- `test_past_departure_date_shows_error_message`
- `test_single_word_name_shows_error_message`
- `test_invalid_submission_preserves_entered_name`
- `test_invalid_submission_shows_error_and_preserves_values`
  (inquire_package variant)

Full suite: 573 passed (569 previous + 4 new), 2 pre-existing warnings
unrelated to this change.
