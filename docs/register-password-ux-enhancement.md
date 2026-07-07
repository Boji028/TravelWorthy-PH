# Register page: compact password requirements + show/hide toggle

**Date:** 2026-07-02

## What changed

`templates/auth/register.html` — full-file replacement.

- Password requirements checklist changed from a boxed 3-row list to a
  compact inline chip row ("8+ chars · Uppercase · Number"), each chip
  turning teal-green with a checkmark live as the user types, same
  behavior as before just less vertical space
- Added a show/hide eye-icon toggle on both the Password and Confirm
  Password fields (`togglePassword()` in the page script)
- Removed the old visual strength bar (`.password-strength` /
  `.strength-fill` / `.strength-text`) — the inline chips already
  communicate progress, so the bar was redundant
- Google sign-in button (added in a previous session) is unchanged
- All existing Jinja form logic, CSRF token, field validation error
  display, and `RegisterForm` field bindings are unchanged

## Why

The original boxed checklist took up significant vertical space and
used static gray dots that didn't visually confirm progress as
requirements were met. This matches the design agreed on in the
in-chat preview iteration (minimal inline chips, live checkmarks, eye
toggle) that had only been mocked up visually but not yet applied to
the real template.

## Notes

`templates/auth/login.html` was not touched — it only has a single
password field (no confirm/match logic), so the compact-chips redesign
doesn't apply there. It already has the Google button from the earlier
OAuth work. The eye-toggle icon could be added to login's single
password field in a follow-up pass for visual consistency, if wanted.
