"""Tests for admin inquiry management routes."""
from datetime import date, timedelta
from models.inquiry import Inquiry
from models.user import User
from werkzeug.security import generate_password_hash


def _make_inquiry(db, **overrides):
    today = date.today()
    defaults = dict(
        name="Test Customer",
        email="customer@example.com",
        contact_number="+639171234567",
        destination="Palawan",
        travel_date_from=today + timedelta(days=10),
        travel_date_to=today + timedelta(days=14),
        num_adults=2,
        status="new",
    )
    defaults.update(overrides)
    inquiry = Inquiry(**defaults)
    db.session.add(inquiry)
    db.session.commit()
    return inquiry


def _make_user(db, **overrides):
    defaults = dict(
        name="Regular User",
        email="user@example.com",
        password=generate_password_hash("TestPass123"),
        is_admin=False,
        email_verified=True,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db.session.add(user)
    db.session.commit()
    return user


class TestUpdateInquiryStatus:
    def test_requires_login(self, client):
        response = client.post("/admin/inquiries/update/1", data={"status": "contacted"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        inquiry = _make_inquiry(db)
        response = authenticated_client.post(f"/admin/inquiries/update/{inquiry.id}", data={"status": "contacted"})
        assert response.status_code in (302, 403)
        assert db.session.get(Inquiry, inquiry.id).status == "new"

    def test_valid_status_update(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db)
        admin_client.post(f"/admin/inquiries/update/{inquiry.id}", data={"status": "contacted"})
        assert db.session.get(Inquiry, inquiry.id).status == "contacted"

    def test_all_valid_statuses_accepted(self, app, admin_client):
        from app import db

        for status in ("new", "contacted", "confirmed", "closed"):
            inquiry = _make_inquiry(db, email=f"{status}@example.com")
            admin_client.post(f"/admin/inquiries/update/{inquiry.id}", data={"status": status})
            assert db.session.get(Inquiry, inquiry.id).status == status

    def test_invalid_status_not_saved(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db)
        admin_client.post(f"/admin/inquiries/update/{inquiry.id}", data={"status": "hacked"})
        assert db.session.get(Inquiry, inquiry.id).status == "new"

    def test_redirects_to_inquiries_list(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db)
        response = admin_client.post(
            f"/admin/inquiries/update/{inquiry.id}",
            data={"status": "contacted"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin/inquiries" in response.headers["Location"]

    def test_nonexistent_inquiry_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/inquiries/update/99999", data={"status": "contacted"})
        assert response.status_code == 404


class TestReplyToInquiry:
    def test_requires_login(self, client):
        response = client.post("/admin/inquiries/reply/1", data={"response": "Hello"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        inquiry = _make_inquiry(db)
        response = authenticated_client.post(f"/admin/inquiries/reply/{inquiry.id}", data={"response": "Hello"})
        assert response.status_code in (302, 403)

    def test_empty_response_does_not_update(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db)
        admin_client.post(f"/admin/inquiries/reply/{inquiry.id}", data={"response": ""})
        updated = db.session.get(Inquiry, inquiry.id)
        assert updated.admin_response is None
        assert updated.status == "new"

    def test_whitespace_response_does_not_update(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db)
        admin_client.post(f"/admin/inquiries/reply/{inquiry.id}", data={"response": "   "})
        assert db.session.get(Inquiry, inquiry.id).admin_response is None

    def test_nonexistent_inquiry_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/inquiries/reply/99999", data={"response": "Hello"})
        assert response.status_code == 404


class TestDeleteInquiry:
    def test_requires_login(self, client):
        response = client.post("/admin/inquiries/delete/1")
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        inquiry = _make_inquiry(db)
        authenticated_client.post(f"/admin/inquiries/delete/{inquiry.id}")
        assert db.session.get(Inquiry, inquiry.id) is not None

    def test_admin_can_delete(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db)
        inquiry_id = inquiry.id
        response = admin_client.post(f"/admin/inquiries/delete/{inquiry_id}")
        assert response.status_code == 302
        assert db.session.get(Inquiry, inquiry_id) is None

    def test_nonexistent_inquiry_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/inquiries/delete/99999")
        assert response.status_code == 404


class TestConfirmationEmailFailedBadge:
    """The admin-facing half of the email-failure fix: a small warning
    icon next to the customer's email on the inquiries list, so staff
    have a way to notice and follow up manually — the only real
    mitigation possible here, since the confirmation email sends
    asynchronously, after the customer's own response has already
    been returned."""

    def test_failed_email_shows_warning_icon(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db, confirmation_email_failed=True)
        response = admin_client.get("/admin/inquiries")
        assert b"Confirmation email failed to send" in response.data

    def test_successful_email_shows_no_warning_icon(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db, confirmation_email_failed=False)
        response = admin_client.get("/admin/inquiries")
        assert b"Confirmation email failed to send" not in response.data
