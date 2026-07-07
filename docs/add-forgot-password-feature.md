# Add forgot password feature

## Problem
The "Forgot password?" link on the login page was a placeholder
(href="#") - the feature was never built, not broken.

## What was built
A full forgot-password / reset-password flow, following the same
pattern as the existing email verification feature for consistency:

1. PasswordResetToken model (models/password_reset.py) - single-use,
   expiring token, same secure-token pattern as EmailVerificationToken
   (secrets.token_urlsafe(64), expires_at, is_used flag).
2. PasswordResetService (password_reset_service.py) - request_reset(),
   _send_reset_email(), reset_password().
3. Two new forms (forms.py): ForgotPasswordForm, ResetPasswordForm
   (reuses the existing StrongPasswordValidator).
4. Two new routes (routes/auth.py): GET/POST /auth/forgot-password,
   GET/POST /auth/reset-password/<token>. Both rate-limited like the
   existing resend-verification route (3/min, 5/hour per email).
5. Two new templates matching the login page's branded style:
   templates/auth/forgot_password.html, templates/auth/reset_password.html.
6. Login page's Forgot password link now points at the real route.

## Security decisions
- The forgot-password form always shows the same generic message
  regardless of whether the email exists, to avoid leaking which
  emails are registered (same approach as resend_verification_email).
- Reset tokens expire in 1 hour (shorter than the 24-hour email
  verification token, since a password reset link is more sensitive).
- Requesting a new reset invalidates any previous unused token for
  that user.
- Google-only accounts (user.password is None) are a silent no-op -
  they get the same generic message, but no email is sent and no
  token is created. They should use "Continue with Google" instead.

## Files changed
- models/password_reset.py - new
- models/__init__.py - registered PasswordResetToken
- password_reset_service.py - new
- forms.py - added ForgotPasswordForm, ResetPasswordForm
- routes/auth.py - added forgot_password, reset_password routes
- templates/auth/forgot_password.html - new
- templates/auth/reset_password.html - new
- templates/auth/login.html - Forgot password link now real
- tests/test_password_reset.py - new (21 tests)

## Verification
- Full suite: 511 passed, 0 failed (490 existing + 21 new).

## Migration required
This adds a new database table. Run on your machine:
```
flask db migrate -m "Add password reset tokens table"
flask db upgrade
```
