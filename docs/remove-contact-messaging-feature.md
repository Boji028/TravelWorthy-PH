# Remove Contact Us messaging feature entirely

**Date:** 2026-07-19

## Why

Boss's decision: Contact Us is no longer a way for visitors to send a
message through the site — it's just a reach-us-details page (phone,
email, office, hours). Full removal requested: public form, backend
route, the `ContactMessage` model/table, and the admin Contact Messages
panel (including the branded reply feature and Cc field built earlier
today) — none of it needed going forward. Existing messages didn't
need to be preserved.

## What changed

**Public page** — `templates/main/contact.html`: removed the "Send Us
a Message" form entirely. Layout changed from a 2-column
info-card + form-card grid to a single centered info card (max-width
640px), since there's only one thing on the page now.

**Route** — `routes/main.py::contact()`: reduced from a GET+POST route
with form validation, DB writes, and async email dispatch down to a
plain `@main_bp.route("/contact")` that just renders the template. No
more `ContactForm`, `ContactMessage`, or rate limiting on this route -
removed the now-unused `ContactMessage`, `ContactForm`, and `limiter`
imports too.

**Admin panel** — `routes/admin.py`: removed all five contact-message
routes (`contact_messages`, `mark_message_read`,
`reply_to_contact_message`, `delete_contact_messages_bulk`,
`delete_contact_message`) and the `ContactMessage` import. Also removed
the message-unlinking step from the user-delete cascade (`ContactMessage
.query.filter_by(user_id=user.id).update({"user_id": None})`) since
there's no longer a table to unlink from.
`templates/admin/contact_messages.html` deleted; the "Messages" link
removed from the admin sidebar (`templates/admin/base_admin.html`).

**Forms** — `forms.py`: removed the `ContactForm` class entirely.

**Model** — `models/contact.py` deleted. Removed its import/export from
`models/__init__.py` and the model-registration import in `app.py`
(the one that makes `db.create_all()` aware of it for local SQLite dev).

**Email service** — `email_service.py`: removed all four
`send_contact_*` functions (`send_contact_autoreply`,
`send_contact_reply`, `send_contact_admin_alert`,
`send_contact_emails_async` — the last two built earlier today).
Removed the now-unused `quote` import (only ever used for the mailto
Subject pre-fill inside `send_contact_admin_alert`).

**Database** — new migration `b4d8f1a6c3e7` drops the
`contact_messages` table outright. `contact_messages` predates Alembic
(no original "create table" migration exists in this repo), so the
`downgrade()` reconstructs the schema by hand from the model as it
stood right before deletion. Verified by manually creating a
legacy-shaped table in a test SQLite DB, stamping at the previous head
(`a1c5e9f3b7d2`), and confirming `flask db upgrade` drops it cleanly.

**Scripts** — `scripts/check_data_integrity.py`: removed
`contact_messages` from the hardcoded table-count summary list.
`scripts/migrate_contact_user.py` deleted outright - a one-off script
for a column on a table that no longer exists.

## Tests

- `tests/test_contact_messages.py` deleted entirely (all admin
  contact-message tests, including everything added for the reply
  feature and Cc field earlier today).
- `tests/test_public_pages.py`: removed the entire `TestContactRoute`
  class (form validation, async email, mailto-link tests) and the now-
  unused `ContactMessage` import. Added a small `TestContactPage` class
  instead - confirms the page renders with the phone/email details,
  confirms the form markup ("Send Us a Message", the `message` field)
  is actually gone, and confirms `POST /contact` now returns 405 since
  the route is GET-only.
- `tests/test_forms.py`: removed `TestContactForm` and the `ContactForm`
  import.

Full suite: 557 passed (down from 593 - net loss of tests reflects the
removed feature, not new gaps; nothing else broke). 2 pre-existing
warnings unrelated to this change.

## Deleted files (won't be removed by extracting the zip - delete manually)

- `models/contact.py`
- `templates/admin/contact_messages.html`
- `scripts/migrate_contact_user.py`
- `tests/test_contact_messages.py`

## Action required before/after deploy

Run `flask db upgrade` after deploying to actually drop the
`contact_messages` table in production.
