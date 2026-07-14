"""Tests for the in-app inquiry notification system.

Covers the InquiryNotification model, the notify_* helper functions in
notification_service.py, the routes that trigger notifications (inquiry
creation, status change, reply), the per-notification mark-as-read
endpoint, and the context processor that feeds the bell dropdown.
"""
import pytest
from datetime import date, timedelta, datetime, timezone
from models.inquiry import Inquiry
from models.inquiry_notification import InquiryNotification
from constants import InquiryStatus


def _valid_inquiry_form_data(**overrides):
    """Form data that satisfies every InquiryForm validator."""
    data = {
        "name": "Test User",
        "email": "testuser@example.com",
        "contact_number": "+639171234567",
        "destination": "Bali",
        "travel_date_from": (date.today() + timedelta(days=30)).isoformat(),
        "travel_date_to": (date.today() + timedelta(days=37)).isoformat(),
        "num_adults": 2,
        "num_children": 0,
        "num_infants": 0,
        "special_requests": "",
    }
    data.update(overrides)
    return data


def _make_inquiry(db, user_id=None, package_id=None, status=InquiryStatus.NEW.value):
    """Create and commit an Inquiry the same way the live routes do."""
    inquiry = Inquiry(
        name="Test User",
        email="testuser@example.com",
        contact_number="+639171234567",
        destination="Bali",
        travel_date_from=date.today() + timedelta(days=30),
        travel_date_to=date.today() + timedelta(days=37),
        num_adults=2,
        num_children=0,
        num_infants=0,
        special_requests="",
        status=status,
        user_id=user_id,
        package_id=package_id,
    )
    db.session.add(inquiry)
    db.session.commit()
    return inquiry


class TestInquiryNotificationModel:
    """Test the InquiryNotification model itself."""

    def test_notification_creation_defaults(self, app, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)

        notif = InquiryNotification(
            user_id=test_user.id, inquiry_id=inquiry.id, message="Your inquiry to Bali is now confirmed."
        )
        db.session.add(notif)
        db.session.commit()

        assert notif.id is not None
        assert notif.is_read is False
        assert notif.created_at is not None
        assert isinstance(notif.created_at, datetime)

    def test_notification_repr(self, app, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)

        notif = InquiryNotification(user_id=test_user.id, inquiry_id=inquiry.id, message="Test message")
        db.session.add(notif)
        db.session.commit()

        rep = repr(notif)
        assert str(test_user.id) in rep
        assert str(inquiry.id) in rep

    def test_notification_relationships(self, app, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)

        notif = InquiryNotification(user_id=test_user.id, inquiry_id=inquiry.id, message="Test message")
        db.session.add(notif)
        db.session.commit()

        assert notif.user.id == test_user.id
        assert notif.inquiry.id == inquiry.id
        assert notif in test_user.inquiry_notifications
        assert notif in inquiry.notifications


class TestNotificationService:
    """Test the notify_* helper functions in notification_service.py."""

    def test_notify_inquiry_created_for_logged_in_user(self, app, test_user):
        from app import db
        from notification_service import notify_inquiry_created

        inquiry = _make_inquiry(db, user_id=test_user.id)

        notify_inquiry_created(inquiry)
        db.session.commit()

        notifs = InquiryNotification.query.filter_by(user_id=test_user.id).all()
        assert len(notifs) == 1
        assert "Bali" in notifs[0].message

    def test_notify_inquiry_created_skips_guest(self, app):
        from app import db
        from notification_service import notify_inquiry_created

        inquiry = _make_inquiry(db, user_id=None)

        notify_inquiry_created(inquiry)
        db.session.commit()

        assert InquiryNotification.query.count() == 0

    def test_notify_inquiry_status_change_for_owner(self, app, test_user):
        from app import db
        from notification_service import notify_inquiry_status_change

        inquiry = _make_inquiry(db, user_id=test_user.id)

        notify_inquiry_status_change(inquiry, "Your inquiry to Bali is now confirmed.")
        db.session.commit()

        notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert notif is not None
        assert notif.message == "Your inquiry to Bali is now confirmed."

    def test_notify_inquiry_status_change_skips_guest(self, app):
        from app import db
        from notification_service import notify_inquiry_status_change

        inquiry = _make_inquiry(db, user_id=None)

        notify_inquiry_status_change(inquiry, "Status changed.")
        db.session.commit()

        assert InquiryNotification.query.count() == 0

    def test_notify_admins_new_inquiry_notifies_every_admin(self, app, admin_user):
        from app import db
        from notification_service import notify_admins_new_inquiry
        from models.user import User
        from werkzeug.security import generate_password_hash

        second_admin = User(
            name="Second Admin",
            email="admin2@example.com",
            password=generate_password_hash("AdminPass123!"),
            is_admin=True,
            email_verified=True,
        )
        db.session.add(second_admin)
        db.session.commit()

        inquiry = _make_inquiry(db, user_id=None)
        notify_admins_new_inquiry(inquiry)
        db.session.commit()

        notified_user_ids = {n.user_id for n in InquiryNotification.query.all()}
        assert notified_user_ids == {admin_user.id, second_admin.id}

    def test_notify_admins_new_inquiry_works_for_guest_inquiries(self, app, admin_user):
        from app import db
        from notification_service import notify_admins_new_inquiry

        inquiry = _make_inquiry(db, user_id=None)

        notify_admins_new_inquiry(inquiry)
        db.session.commit()

        notif = InquiryNotification.query.filter_by(user_id=admin_user.id).first()
        assert notif is not None
        assert "Test User" in notif.message

    def test_notify_users_new_package_notifies_every_non_admin(self, app, test_user, admin_user, test_package):
        from app import db
        from notification_service import notify_users_new_package
        from models.user import User
        from werkzeug.security import generate_password_hash

        second_user = User(
            name="Second User",
            email="seconduser@example.com",
            password=generate_password_hash("TestPass123!"),
            is_admin=False,
            email_verified=True,
        )
        db.session.add(second_user)
        db.session.commit()

        notify_users_new_package(test_package)
        db.session.commit()

        notified_user_ids = {n.user_id for n in InquiryNotification.query.all()}
        assert notified_user_ids == {test_user.id, second_user.id}
        assert admin_user.id not in notified_user_ids

    def test_notify_users_new_package_sets_message_and_link(self, app, test_user, test_package):
        from app import db
        from notification_service import notify_users_new_package

        notify_users_new_package(test_package)
        db.session.commit()

        notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert notif is not None
        assert test_package.title in notif.message
        assert notif.inquiry_id is None
        assert notif.link_url == f"/packages/{test_package.id}"

    def test_notify_users_new_visa_notifies_every_non_admin(self, app, test_user, admin_user):
        from app import db
        from notification_service import notify_users_new_visa
        from models.visa import VisaCountry

        visa = VisaCountry(country_name="Japan", is_active=True)
        db.session.add(visa)
        db.session.commit()

        notify_users_new_visa(visa)
        db.session.commit()

        notified_user_ids = {n.user_id for n in InquiryNotification.query.all()}
        assert notified_user_ids == {test_user.id}
        assert admin_user.id not in notified_user_ids

    def test_notify_users_new_visa_sets_message_and_link(self, app, test_user):
        from app import db
        from notification_service import notify_users_new_visa
        from models.visa import VisaCountry

        visa = VisaCountry(country_name="Japan", is_active=True)
        db.session.add(visa)
        db.session.commit()

        notify_users_new_visa(visa)
        db.session.commit()

        notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert notif is not None
        assert "Japan" in notif.message
        assert notif.link_url == "/packages/visa"


class TestNewContentNotificationRoutes:
    """Test that adding a package or visa entry through the real admin
    routes broadcasts an in-app notification to every non-admin user."""

    def test_add_package_notifies_registered_users_not_admin(self, admin_client, test_user, admin_user):
        response = admin_client.post(
            "/admin/packages/add",
            data=dict(
                title="Palawan Adventure",
                description="Explore beautiful Palawan islands.",
                destination="Palawan",
                duration_days="5",
                price="9999",
                currency="PHP",
            ),
            follow_redirects=False,
        )
        assert response.status_code == 302

        user_notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert user_notif is not None
        assert "Palawan Adventure" in user_notif.message

        admin_notif = InquiryNotification.query.filter_by(user_id=admin_user.id).first()
        assert admin_notif is None

    def test_add_visa_notifies_registered_users_not_admin(self, admin_client, test_user, admin_user):
        response = admin_client.post(
            "/admin/visa/add", data={"country_name": "Japan", "is_active": "on"}, follow_redirects=False
        )
        assert response.status_code == 302

        user_notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert user_notif is not None
        assert "Japan" in user_notif.message

        admin_notif = InquiryNotification.query.filter_by(user_id=admin_user.id).first()
        assert admin_notif is None


class TestInquiryCreationNotifications:
    """Test that submitting an inquiry through the real routes creates the right notifications."""

    def test_plan_my_trip_notifies_logged_in_user(self, authenticated_client, test_user, admin_user):
        response = authenticated_client.post("/bookings/plan-my-trip", data=_valid_inquiry_form_data(), follow_redirects=False)
        assert response.status_code == 302

        user_notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert user_notif is not None
        assert "Bali" in user_notif.message

        admin_notif = InquiryNotification.query.filter_by(user_id=admin_user.id).first()
        assert admin_notif is not None
        assert "Test User" in admin_notif.message

    def test_plan_my_trip_guest_gets_no_user_notification_but_admin_does(self, client, admin_user):
        response = client.post("/bookings/plan-my-trip", data=_valid_inquiry_form_data(), follow_redirects=False)
        assert response.status_code == 302

        guest_notifs = InquiryNotification.query.filter(InquiryNotification.user_id != admin_user.id).all()
        assert guest_notifs == []

        admin_notif = InquiryNotification.query.filter_by(user_id=admin_user.id).first()
        assert admin_notif is not None

    def test_inquire_package_notifies_logged_in_user(self, authenticated_client, test_user, test_package, admin_user):
        response = authenticated_client.post(
            f"/bookings/inquire/{test_package.id}", data=_valid_inquiry_form_data(), follow_redirects=False
        )
        assert response.status_code == 302

        user_notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert user_notif is not None

        inquiry = Inquiry.query.filter_by(package_id=test_package.id).first()
        assert inquiry is not None
        assert inquiry.user_id == test_user.id


class TestInquiryUpdateNotifications:
    """Test that admin actions on an inquiry notify its owner."""

    def test_status_update_to_confirmed_notifies_owner(self, app, admin_client, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id, status=InquiryStatus.NEW.value)

        response = admin_client.post(
            f"/admin/inquiries/update/{inquiry.id}", data={"status": InquiryStatus.CONFIRMED.value}, follow_redirects=False
        )
        assert response.status_code == 302

        notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert notif is not None
        assert InquiryStatus.CONFIRMED.value in notif.message

    def test_status_update_to_same_status_does_not_duplicate_notification(self, app, admin_client, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id, status=InquiryStatus.CONFIRMED.value)

        admin_client.post(
            f"/admin/inquiries/update/{inquiry.id}", data={"status": InquiryStatus.CONFIRMED.value}, follow_redirects=False
        )

        assert InquiryNotification.query.filter_by(user_id=test_user.id).count() == 0

    def test_reply_notifies_owner(self, app, admin_client, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)

        admin_client.post(
            f"/admin/inquiries/reply/{inquiry.id}",
            data={"response": "Thanks for reaching out, we have a great package for Bali!"},
            follow_redirects=False,
        )

        notif = InquiryNotification.query.filter_by(user_id=test_user.id).first()
        assert notif is not None
        assert "replied" in notif.message.lower()


class TestMarkNotificationRead:
    """Test the per-notification mark-as-read endpoint."""

    def test_marks_own_notification_as_read(self, app, authenticated_client, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)
        notif = InquiryNotification(user_id=test_user.id, inquiry_id=inquiry.id, message="Test")
        db.session.add(notif)
        db.session.commit()

        response = authenticated_client.post(f"/notifications/{notif.id}/mark-read")
        assert response.status_code == 200
        assert response.get_json()["success"] is True

        db.session.refresh(notif)
        assert notif.is_read is True

    def test_cannot_mark_another_users_notification_as_read(self, app, authenticated_client, admin_user):
        """Security: a user hitting another user's notification ID should
        not be able to mark it read."""
        from app import db

        inquiry = _make_inquiry(db, user_id=admin_user.id)
        notif = InquiryNotification(user_id=admin_user.id, inquiry_id=inquiry.id, message="Not yours")
        db.session.add(notif)
        db.session.commit()

        response = authenticated_client.post(f"/notifications/{notif.id}/mark-read")
        assert response.status_code == 200

        db.session.refresh(notif)
        assert notif.is_read is False

    def test_mark_read_requires_login(self, client, app, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)
        notif = InquiryNotification(user_id=test_user.id, inquiry_id=inquiry.id, message="Test")
        db.session.add(notif)
        db.session.commit()

        response = client.post(f"/notifications/{notif.id}/mark-read")
        assert response.status_code in (302, 401)


class TestNotificationContextProcessor:
    """Test the inject_notifications context processor that feeds the bell dropdown."""

    def test_only_unread_notifications_appear(self, app, authenticated_client, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)

        unread = InquiryNotification(user_id=test_user.id, inquiry_id=inquiry.id, message="Unread one")
        read = InquiryNotification(user_id=test_user.id, inquiry_id=inquiry.id, message="Read one", is_read=True)
        db.session.add_all([unread, read])
        db.session.commit()

        response = authenticated_client.get("/")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert "Unread one" in page
        assert "Read one" not in page

    def test_unread_count_matches_badge(self, app, authenticated_client, test_user):
        from app import db

        inquiry = _make_inquiry(db, user_id=test_user.id)

        for i in range(3):
            db.session.add(InquiryNotification(user_id=test_user.id, inquiry_id=inquiry.id, message=f"Msg {i}"))
        db.session.commit()

        response = authenticated_client.get("/")
        page = response.get_data(as_text=True)
        assert 'class="notif-badge"' in page

    def test_anonymous_user_sees_no_notifications(self, client):
        response = client.get("/")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'class="notif-badge"' not in page

    def test_link_url_notification_links_to_link_url_not_admin_fallback(self, app, authenticated_client, test_user):
        """A system-wide, non-inquiry notification with link_url set (e.g.
        new package announcement) should link there — not fall through to
        the admin inquiries page, which a regular user can't even access."""
        from app import db

        notif = InquiryNotification(
            user_id=test_user.id,
            inquiry_id=None,
            message="New tour package added: Palawan Adventure — check it out!",
            link_url="/packages/1",
        )
        db.session.add(notif)
        db.session.commit()

        response = authenticated_client.get("/")
        page = response.get_data(as_text=True)
        assert 'href="/packages/1"' in page
        assert "New tour package added" in page

    def test_non_admin_notification_with_no_link_and_no_inquiry_never_links_to_admin_page(
        self, app, authenticated_client, test_user
    ):
        """No current code path creates a notification with both
        inquiry_id and link_url unset for a non-admin user — every
        producer sets one or the other. But nothing in the model enforces
        that, so this is a defensive test: if that combination ever did
        occur (a future bug), a regular user must never be routed to
        /admin/inquiries, which they don't have permission to view."""
        from app import db

        notif = InquiryNotification(
            user_id=test_user.id,
            inquiry_id=None,
            message="Some hypothetical system notification",
            link_url=None,
        )
        db.session.add(notif)
        db.session.commit()

        response = authenticated_client.get("/")
        page = response.get_data(as_text=True)
        assert "/admin/inquiries" not in page
        assert 'href="/my-inquiries"' in page
