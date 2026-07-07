# Contact form fix

## Problem
Contact form silently failed on every submission — page refreshed with no
flash message and no error shown to the user.

## Root cause
Two issues found via debug logging:

1. Email() validator from wtforms silently fails in newer versions of
   email-validator (2.x) unless granular_message=False is passed.
   All four Email() usages in forms.py were updated.

2. Subject field had min=5 but the validator error was hidden from the
   user since the template only shows form.message.errors, not
   form.subject.errors. Lowered min to 2 to match other short fields.

## Files changed
- forms.py — Email(granular_message=False) on all four validators;
  subject min length lowered from 5 to 2
- routes/main.py — removed temporary debug logging