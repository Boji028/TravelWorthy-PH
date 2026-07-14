# Close the two flagged-not-fixed items from the pre-deploy pass

## Context
The pre-deploy bug-hunt pass (`docs/activity-log.md`, 2026-07-14 entry)
flagged two things as real but not urgent enough to fix on its own:
notification broadcast doing one INSERT per user, and a rate-limit
`key_func` calling `.lower()` on a value that's typed `Optional[str]`.
Neither was an active bug in the current deployment, but "theoretically
possible" isn't the same as "comfortable to ship" — closing both.

## 1. Rate-limit key_func crash on missing remote_addr
`routes/auth.py`: `resend_verification` and `forgot_password` both had
```python
key_func=lambda: request.form.get("email", request.remote_addr).lower()
```
`request.remote_addr` is `Optional[str]` — if a request has no `email`
form field *and* `remote_addr` is unavailable, `.get()` returns `None`
and `.lower()` throws `AttributeError`, which Flask-Limiter doesn't
catch — it surfaces as an uncaught 500 during request dispatch, before
the view function's own validation ever runs. The pre-deploy pass
correctly assessed this as unreachable behind gunicorn/TCP specifically
(peer address is always populated there), but that's one deployment
detail away from being wrong, and it's a two-token fix regardless.

Fix:
```python
key_func=lambda: (request.form.get("email", request.remote_addr) or "unknown").lower()
```
Preserves the original two-argument `.get()` semantics (the default is
only used when the `email` key is absent, not when it's an empty
string) and just guards the final `.lower()` call.

**Verified this was a real, reachable bug**, not just a theoretical
type-checker complaint: reverted the fix locally and confirmed both new
regression tests fail with exactly the predicted
`AttributeError: 'NoneType' object has no attribute 'lower'`, then
restored the fix and confirmed they pass. Tests use
`environ_overrides={"REMOTE_ADDR": None}` to simulate the missing
value directly rather than trying to reproduce a specific deployment
topology.

## 2. Notification broadcast: bulk insert instead of per-user ORM add
`notification_service.py`: `notify_users_new_package()` and
`notify_users_new_visa()` looped over every non-admin user, creating
one `InquiryNotification()` ORM object and one `session.add()` call
each. Correct at current scale (hundreds of users), but each object add
is tracked individually by the ORM's unit-of-work and turns into N
separate INSERT statements at flush time — a slow admin request once
the user base reaches the thousands.

Rewrote both to build a list of plain dicts and issue one
`db.session.execute(insert(InquiryNotification), rows)` — SQLAlchemy
Core's bulk-insert path, a single statement (executemany at the driver
level) regardless of user count. Same external behavior: same columns,
same values, same "doesn't commit, caller commits" contract. Existing
tests for both functions (added when the notification feature was
first built) passed unchanged against the new implementation, since
they only assert on the resulting rows, not the insert mechanism.

## 3. Hardened the latent template edge case
The pre-deploy pass's section 3c noted: a notification with neither
`inquiry_id` nor `link_url`, sent to a non-admin, would fall through to
`admin.inquiries` — a page that user can't access — but confirmed no
current producer creates that combination. Cheap insurance regardless:
`templates/base.html`'s notification dropdown now branches on
`current_user.is_admin` for the fallback case, so a non-admin lands on
`main.my_inquiries` instead of the admin-only page even if some future
notification type is added without setting one of those two fields.

## Verification
- Full suite: 542/542 passing (539 baseline + 3 new tests: two
  key_func regression tests, one template-hardening test).
- Confirmed the key_func regression tests are genuine (fail on the old
  code, pass on the fix) rather than trivially-passing, by reverting
  the fix, re-running, and restoring it — see above.
