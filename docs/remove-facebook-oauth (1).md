# Remove Facebook sign-in, keep Google-only OAuth

**Date:** 2026-07-02

## What changed

Removed Facebook as a sign-in option, leaving Google as the only OAuth
provider alongside standard email/password registration.

- `templates/auth/login.html` — replaced the two-button Google/Facebook
  grid with a single full-width "Continue with Google" button
- `templates/auth/register.html` — same swap on the sign-up form
- `routes/auth.py` — removed `facebook_login()` and `facebook_callback()`
  routes entirely; `google_login()`, `google_callback()`, and the shared
  `_oauth_login()` helper are unchanged
- `oauth.py` — removed the Facebook client registration block from
  `init_oauth()`; Google registration is unchanged
- `.env` — removed `FACEBOOK_CLIENT_ID` / `FACEBOOK_CLIENT_SECRET`

No database migration needed — `User.oauth_provider` is a plain string
column with no enum/check constraint, so it simply never gets set to
`'facebook'` going forward. Existing rows are unaffected.

## Why

Simplifies the OAuth surface to one provider. Also removes the
account-linking edge case that existed only for Facebook: since
Facebook's returned email isn't verified as reliably as Google's, the
original implementation deliberately never auto-linked a Facebook
identity to an existing email/password account (see
`docs/oauth-google-facebook-signin.md` if that file exists from the
original build-out — otherwise this note stands on its own). That
whole code path — and the manual "log in with password first, then
connect Facebook from your profile" flow it implied — no longer exists
since there's nothing to connect.

## Follow-up

None required. If Facebook sign-in is wanted again later, the removed
code is recoverable from git history (`git log -p -- routes/auth.py
oauth.py`) rather than rewritten from scratch.
