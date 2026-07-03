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
