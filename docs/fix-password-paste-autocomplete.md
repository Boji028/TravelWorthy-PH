# Fix inconsistent password paste on Create Account

## Problem
Pasting into the Password / Confirm Password fields on the Create
Account page sometimes kept the pasted value and sometimes silently
replaced it with something else.

## Root cause
templates/auth/register.html - the password and confirm_password
inputs had no autocomplete attribute. Browsers (Chrome in particular)
use autocomplete hints to decide whether a password field is a login
field or a new-password field. Without new-password, the browser's
own "suggest a strong password" feature or saved-credential autofill
can kick in after a paste and overwrite the field - inconsistently,
depending on browser heuristics and whether a saved credential exists
for the site.

## Fix
Added autocomplete="new-password" to both the password and
confirm_password inputs. This tells the browser these are new-password
fields, not login fields, so it stops trying to autofill or suggest
its own value over what the user typed or pasted.

## Files changed
- templates/auth/register.html - autocomplete="new-password" added to
  both password inputs

## Verification
- tests/test_auth.py: 14 passed (attribute-only change, no backend
  logic affected).

## Notes
templates/auth/login.html also has no autocomplete attribute on its
password field, but that is not the same bug - autofilling a saved
credential is the wanted behavior on login. Not touched here.