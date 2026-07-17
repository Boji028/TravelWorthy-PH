# Contact page: migration gap + missing validation errors

**Date:** 2026-07-17

## Issue 1: "Could not send your message" banner

Not a code bug - a pending migration. The reply feature shipped earlier
today added `admin_response`/`responded_at` columns to `ContactMessage`.
Any environment that hasn't run `flask db upgrade` since then still has
the old `contact_messages` table shape, so every insert throws
`OperationalError: table contact_messages has no column named
admin_response`. `routes/main.py::contact()` catches that in its generic
`except Exception` and flashes "Could not send your message. Please try
again later." - reproduced exactly by hand-building the old table shape
and inserting through the current model.

**Fix:** run `flask db upgrade` in the affected environment. No code
change needed.

## Issue 2: contact form silently re-rendered on validation failure

Same underlying bug already fixed on the inquiry forms
(`inquiry-form-validation-error-display-fix.md`), just not yet applied
here. `templates/main/contact.html` showed an error for `message` only -
`name`, `email`, and `subject` had no `{% if form.field.errors %}` block
and no `value="{{ form.field.data }}"` binding, so a validation failure
(most commonly `FullNameValidator` rejecting a single-word name) just
redisplayed a blank form with zero explanation, and wiped out the
`message` textarea's content too despite showing its own error.

**Fix:** brought all four fields in line with the same pattern already
used on the inquiry forms and register.html - value binding to preserve
input, error text under the field that failed.

## Tests

Added to `tests/test_public_pages.py` (`TestContactRoute`):
- `test_single_word_name_shows_error_message`
- `test_invalid_submission_preserves_entered_values`

Full suite: 584 passed (582 previous + 2 new), 2 pre-existing warnings
unrelated to this change.
