# Notify registered users when a new package or visa is added

## Feature
When an admin adds a new tour package or a new visa country, every
non-admin registered user gets an in-app notification in the existing
bell dropdown — no new UI, this reuses the notification system already
built for inquiries.

## What was reused vs. added
`InquiryNotification` was already a generic per-user notification
table (despite the name — it's used for both customer-facing and
admin-facing events, see `notification_service.py`). Broadcasting to
"every registered user" is the exact same shape as the existing
`notify_admins_new_inquiry()` (loops over admins), just inverted to
loop over non-admins instead. Two new functions in
`notification_service.py`:

- `notify_users_new_package(package)`
- `notify_users_new_visa(visa)`

Both follow the established pattern exactly: don't commit (caller
commits alongside its own change), skip nothing special on the
sender's end since these aren't tied to a specific inquiry
(`inquiry_id=None`, same as the existing "inquiries expiring soon"
admin warning). Admins are excluded from the broadcast — they're the
one adding the content, notifying them about their own action would be
noise.

Wired into `routes/admin.py`: `add_package()` and `visa_add()`, right
after each one's existing `db.session.commit()`, in their own
try/except that rolls back and logs a warning on failure without
blocking the actual package/visa creation — copied directly from how
`routes/bookings.py` already handles `notify_inquiry_created` /
`notify_admins_new_inquiry` around inquiry submission.

## Why a new column instead of reusing the existing logic
The dropdown template (`base.html`) previously decided where a
notification links to with only two states: "has an inquiry the
current user owns" → track-inquiry page, or "anything else" → the
admin inquiries list. That second bucket only ever held admin-facing
system notifications before now (e.g. "N inquiries expiring soon"), so
it was safe to hardcode.

A "new package added" notification going to a *regular* user doesn't
fit either bucket — it's not about an inquiry, and it shouldn't link
to `admin.inquiries` (a page most users can't even access). Rather
than inferring the right link from `current_user.is_admin` in the
template (fragile — it works today only because admin-facing and
user-facing system notifications happen to never overlap for the same
person, and that's an assumption a future notification type could
silently break), added an explicit nullable `link_url` column to
`InquiryNotification`. It's opt-in: every existing notification type
leaves it null and keeps using the old inquiry-id-based logic
unchanged. Only the two new functions set it —
`packages.package_detail` for a new package, `packages.visa` for a new
visa entry. Template now checks `link_url` first, before falling back
to the original logic:

```
{% if n.link_url %}
  <a href="{{ n.link_url }}">
{% elif n.inquiry and n.inquiry.user_id == current_user.id %}
  <a href="{{ url_for('main.track_inquiry', ...) }}">
{% else %}
  <a href="{{ url_for('admin.inquiries') }}">
{% endif %}
```

## Migration — read this before running `flask db migrate`
While tracing which revision to chain a new migration from, found that
`migrations/versions/` currently has **three unmerged heads**:
`d1a8f8c3b2a1` (email verification), `a7c3f9e2b1d4` (inquiry
last_exported_at / notification inquiry_id nullable), `e3f7a9c1d2b5`
(reference_number on inquiries). This is a pre-existing issue, not
something this session introduced — it means `flask db upgrade` against
a real database will fail with "Multiple head revisions are present"
until it's resolved. It hasn't surfaced yet because the test suite
uses `db.create_all()` on SQLite (bypasses Alembic entirely, per the
guard condition in `app.py`), so it's only ever hit against Postgres.

**Before touching this feature's migration**, run, on the machine with
the real dev/production database:
```
flask db merge heads -m "merge migration heads"
flask db upgrade
```
This creates a no-op merge revision unifying all three heads — safe,
doesn't touch any table data.

**Then**, for this feature's actual schema change (the `link_url`
column), since the model change is already in place in
`models/inquiry_notification.py`:
```
flask db migrate -m "add link_url to inquiry_notifications"
flask db upgrade
```
Letting Flask-Migrate autogenerate this one (rather than hand-writing
the migration file) sidesteps needing to guess the correct
`down_revision` after the merge — it reads directly off the actual
current head in your database.

## Verification
- Full test suite: 536/536 passing (was 529; +7 new: two
  `notify_users_new_*` unit tests each covering non-admin-only
  targeting and message/link content, two route-level tests posting to
  `/admin/packages/add` and `/admin/visa/add` confirming the broadcast
  fires and admins are excluded, one template test confirming
  `link_url` takes priority over the admin fallback).

## Known minor limitation
If a package or visa entry is deleted after users were notified about
it, the notification's `link_url` goes stale (404 on click). Not
handled defensively here — same class of edge case as an inquiry being
deleted after its own notification exists, which the existing system
also doesn't guard against.
