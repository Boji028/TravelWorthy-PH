"""Tests for the redesigned admin Contact Messages page.

Covers search/filter query params, unread/read status counts, the
AJAX mark-as-read route, and both single and bulk delete.
"""
import pytest
from models.contact import ContactMessage


def _make_contact_message(db, **overrides):
    defaults = dict(
        name="Maria Santos",
        email="maria.santos@example.com",
        subject="Package inquiry",
        message="I wanted to ask about the Palawan island hopping package.",
        is_read=False,
    )
    defaults.update(overrides)
    msg = ContactMessage(**defaults)
    db.session.add(msg)
    db.session.commit()
    return msg


class TestContactMessagesAccess:
    """Non-admins should never reach these routes."""

    def test_list_requires_login(self, client):
        response = client.get("/admin/contact-messages")
        assert response.status_code in (302, 401, 403)

    def test_list_rejects_non_admin_user(self, authenticated_client):
        response = authenticated_client.get("/admin/contact-messages")
        assert response.status_code in (302, 403)

    def test_mark_read_requires_login(self, app, client):
        from app import db

        msg = _make_contact_message(db)
        response = client.post(f"/admin/contact-messages/mark-read/{msg.id}")
        assert response.status_code in (302, 401, 403)

    def test_delete_requires_login(self, app, client):
        from app import db

        msg = _make_contact_message(db)
        response = client.post(f"/admin/contact-messages/delete/{msg.id}")
        assert response.status_code in (302, 401, 403)

    def test_reply_requires_login(self, app, client):
        from app import db

        msg = _make_contact_message(db)
        response = client.post(f"/admin/contact-messages/reply/{msg.id}", data={"response": "Hello"})
        assert response.status_code in (302, 401, 403)

    def test_reply_rejects_non_admin(self, app, authenticated_client):
        from app import db

        msg = _make_contact_message(db)
        response = authenticated_client.post(f"/admin/contact-messages/reply/{msg.id}", data={"response": "Hello"})
        assert response.status_code in (302, 403)


class TestContactMessagesFiltering:
    def test_search_filters_by_name(self, app, admin_client):
        from app import db

        _make_contact_message(db, name="Maria Santos", email="maria.santos@example.com", subject="Subject A")
        _make_contact_message(db, name="Jon Reyes", email="jon.reyes@example.com", subject="Subject B")

        response = admin_client.get("/admin/contact-messages?search=Maria")
        page = response.get_data(as_text=True)
        assert "Maria Santos" in page
        assert "Jon Reyes" not in page

    def test_search_filters_by_email(self, app, admin_client):
        from app import db

        _make_contact_message(db, name="Maria Santos", email="maria@example.com")
        _make_contact_message(db, name="Jon Reyes", email="jon@example.com")

        response = admin_client.get("/admin/contact-messages?search=jon@example.com")
        page = response.get_data(as_text=True)
        assert "Jon Reyes" in page
        assert "Maria Santos" not in page

    def test_search_filters_by_subject(self, app, admin_client):
        from app import db

        _make_contact_message(db, name="Maria Santos", subject="Visa processing time")
        _make_contact_message(db, name="Jon Reyes", subject="Refund request")

        response = admin_client.get("/admin/contact-messages?search=Visa")
        page = response.get_data(as_text=True)
        assert "Maria Santos" in page
        assert "Jon Reyes" not in page

    def test_status_filter_unread(self, app, admin_client):
        from app import db

        _make_contact_message(db, name="Unread Person", is_read=False)
        _make_contact_message(db, name="Read Person", is_read=True)

        response = admin_client.get("/admin/contact-messages?status=unread")
        page = response.get_data(as_text=True)
        assert "Unread Person" in page
        assert "Read Person" not in page

    def test_status_filter_read(self, app, admin_client):
        from app import db

        _make_contact_message(db, name="Unread Person", is_read=False)
        _make_contact_message(db, name="Read Person", is_read=True)

        response = admin_client.get("/admin/contact-messages?status=read")
        page = response.get_data(as_text=True)
        assert "Read Person" in page
        assert "Unread Person" not in page

    def test_status_counts_reflect_search(self, app, admin_client):
        from app import db

        _make_contact_message(db, name="Maria Santos", email="maria.santos@example.com", is_read=False)
        _make_contact_message(db, name="Maria Reyes", email="maria.reyes@example.com", is_read=True)
        _make_contact_message(db, name="Jon Cruz", email="jon.cruz@example.com", is_read=False)

        response = admin_client.get("/admin/contact-messages?search=Maria")
        page = response.get_data(as_text=True)
        assert "All 2" in page
        assert "Unread 1" in page
        assert "Read 1" in page


class TestContactMessageMarkRead:
    def test_mark_read_sets_is_read_and_returns_json(self, app, admin_client):
        from app import db

        msg = _make_contact_message(db, is_read=False)

        response = admin_client.post(f"/admin/contact-messages/mark-read/{msg.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        db.session.refresh(msg)
        assert msg.is_read is True


class TestContactMessageDelete:
    def test_admin_can_delete_single_message(self, app, admin_client):
        from app import db

        msg = _make_contact_message(db)
        msg_id = msg.id

        response = admin_client.post(f"/admin/contact-messages/delete/{msg_id}")
        assert response.status_code == 302
        assert db.session.get(ContactMessage, msg_id) is None

    def test_non_admin_cannot_delete(self, app, authenticated_client):
        from app import db

        msg = _make_contact_message(db)
        msg_id = msg.id

        response = authenticated_client.post(f"/admin/contact-messages/delete/{msg_id}")
        assert response.status_code in (302, 403)
        assert db.session.get(ContactMessage, msg_id) is not None


class TestContactMessageBulkDelete:
    def test_bulk_delete_removes_selected_messages(self, app, admin_client):
        from app import db

        msg1 = _make_contact_message(db, name="Delete Me One")
        msg2 = _make_contact_message(db, name="Delete Me Two")
        msg3 = _make_contact_message(db, name="Keep Me")
        ids_to_delete = [msg1.id, msg2.id]
        keep_id = msg3.id

        response = admin_client.post("/admin/contact-messages/delete-bulk", data={"message_ids": ids_to_delete})
        assert response.status_code == 302
        assert db.session.get(ContactMessage, ids_to_delete[0]) is None
        assert db.session.get(ContactMessage, ids_to_delete[1]) is None
        assert db.session.get(ContactMessage, keep_id) is not None

    def test_bulk_delete_with_no_selection_deletes_nothing(self, app, admin_client):
        from app import db

        msg = _make_contact_message(db, name="Untouched")
        msg_id = msg.id

        response = admin_client.post("/admin/contact-messages/delete-bulk", data={})
        assert response.status_code == 302
        assert db.session.get(ContactMessage, msg_id) is not None


class TestContactMessageReply:
    def test_empty_response_does_not_update(self, app, admin_client):
        from app import db

        msg = _make_contact_message(db)
        admin_client.post(f"/admin/contact-messages/reply/{msg.id}", data={"response": ""})
        updated = db.session.get(ContactMessage, msg.id)
        assert updated.admin_response is None
        assert updated.responded_at is None

    def test_whitespace_response_does_not_update(self, app, admin_client):
        from app import db

        msg = _make_contact_message(db)
        admin_client.post(f"/admin/contact-messages/reply/{msg.id}", data={"response": "   "})
        assert db.session.get(ContactMessage, msg.id).admin_response is None

    def test_nonexistent_message_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/contact-messages/reply/99999", data={"response": "Hello"})
        assert response.status_code == 404

    def test_mail_not_configured_does_not_save_response(self, app, admin_client):
        """Regression test - the old mailto: 'Reply to sender' link had no
        way to fail visibly. This route sends first and only persists on
        success, so an unconfigured mail setup must not silently record a
        reply that was never actually sent."""
        from app import db

        msg = _make_contact_message(db)
        response = admin_client.post(
            f"/admin/contact-messages/reply/{msg.id}", data={"response": "Thanks for reaching out!"}
        )
        assert response.status_code == 302
        updated = db.session.get(ContactMessage, msg.id)
        assert updated.admin_response is None
        assert updated.responded_at is None

    def test_successful_reply_saves_response_and_sends_branded_email(self, app, admin_client, monkeypatch):
        """The whole point of this feature - unlike the plain mailto: reply,
        this must actually go out through the app with the branded HTML
        template, and be recorded on the message."""
        from app import db, mail as app_mail

        app.config["MAIL_USERNAME"] = "test@example.com"
        sent_messages = []
        monkeypatch.setattr(app_mail, "send", lambda m: sent_messages.append(m))

        msg = _make_contact_message(db, name="Maria Santos", subject="Palawan package", is_read=False)
        response = admin_client.post(
            f"/admin/contact-messages/reply/{msg.id}",
            data={"response": "Thanks for reaching out! Here are the details you asked for."},
        )
        assert response.status_code == 302

        updated = db.session.get(ContactMessage, msg.id)
        assert updated.admin_response == "Thanks for reaching out! Here are the details you asked for."
        assert updated.responded_at is not None
        assert updated.is_read is True

        assert len(sent_messages) == 1
        sent = sent_messages[0]
        assert sent.subject == "Re: Palawan package"
        assert sent.recipients == [msg.email]
        assert "Thanks for reaching out!" in sent.body
        assert sent.html is not None and "Thanks for reaching out!" in sent.html

    def test_replied_message_shows_badge_on_list_page(self, app, admin_client, monkeypatch):
        """Regression test for the template render itself - the 'Replied'
        badge reads msg.responded_at.strftime(...), which would crash the
        whole page if responded_at were ever left unset."""
        from app import db, mail as app_mail

        app.config["MAIL_USERNAME"] = "test@example.com"
        monkeypatch.setattr(app_mail, "send", lambda m: None)

        msg = _make_contact_message(db, name="Maria Santos")
        admin_client.post(f"/admin/contact-messages/reply/{msg.id}", data={"response": "Thanks!"})

        response = admin_client.get("/admin/contact-messages")
        assert response.status_code == 200
        assert b"Replied" in response.data
