# Cascade fix: deleting a user with password-reset or verification tokens

## What was wrong
`PasswordResetToken.user` and `EmailVerificationToken.user` were plain
`db.relationship("User", backref=...)` declarations pointing at NOT NULL
`user_id` foreign keys with no cascade configured. This is the exact pattern
documented in CLAUDE.md's Known Pitfalls: on `db.session.delete(user)`,
SQLAlchemy tries to null the child FK instead of deleting the row, which
raises IntegrityError on a NOT NULL column.

The admin `delete_user` route manually bulk-deletes EmailVerificationToken
and InquiryNotification rows before deleting the user, but never
PasswordResetToken. So deleting any user who had ever requested a password
reset (and whose token rows had not yet been purged) crashed with a 500.

## Fix
Added `cascade="all, delete-orphan"` to the backref on both token models,
matching the pattern already used by InquiryNotification, PackageImage and
PackageReview after the earlier production incident:

- `models/password_reset.py` — `User.password_reset_tokens` backref
- `models/email_verification.py` — `User.verification_tokens` backref
  (defense in depth; the route's manual delete also still runs)

## Why the fix is correct
The ORM-level cascade deletes the dependent token rows in the same flush as
the user delete, so the NOT NULL FK is never nulled. Tokens are purely
functional records with nothing worth preserving after the account is gone.

## Tests
`tests/test_cascade_deletes.py` — new `TestUserDeleteWithAuthTokens` class:
deleting a user with a PasswordResetToken (previously a live 500) and with
an EmailVerificationToken now succeeds and removes the token rows.
