"""Tests for notification mark-read routes."""
from datetime import date, timedelta
from models.inquiry import Inquiry
from models.inquiry_notification import InquiryNotification


def _make_inquiry(db, user_id=None):
    today = date.today()
    inquiry = Inquiry(
        name='Customer',
        email='customer@example.com',
        contact_number='+639171234567',
        destination='Palawan',
        travel_date_from=today + timedelta(days=10),
        travel_date_to=today + timedelta(days=14),
        num_adults=2,
        status='new',
        user_id=user_id,
    )
    db.session.add(inquiry)
    db.session.commit()
    return inquiry


def _make_notification(db, user_id, inquiry_id, is_read=False):
    notif = InquiryNotification(
        user_id=user_id,
        inquiry_id=inquiry_id,
        message='Your inquiry status changed.',
        is_read=is_read,
    )
    db.session.add(notif)
    db.session.commit()
    return notif


class TestMarkAllNotificationsRead:
    def test_requires_login(self, client):
        response = client.post('/notifications/mark-read')
        assert response.status_code in (302, 401, 403)

    def test_marks_all_unread_as_read(self, app, authenticated_client, test_user):
        from app import db
        inquiry = _make_inquiry(db, user_id=test_user.id)
        n1 = _make_notification(db, test_user.id, inquiry.id, is_read=False)
        n2 = _make_notification(db, test_user.id, inquiry.id, is_read=False)
        response = authenticated_client.post('/notifications/mark-read')
        assert response.status_code == 200
        assert response.get_json()['success'] is True
        assert db.session.get(InquiryNotification, n1.id).is_read is True
        assert db.session.get(InquiryNotification, n2.id).is_read is True

    def test_does_not_affect_other_users_notifications(self, app, authenticated_client, test_user):
        from app import db
        from models.user import User
        from werkzeug.security import generate_password_hash
        other = User(
            name='Other', email='other@example.com',
            password=generate_password_hash('Pass123'), email_verified=True,
        )
        db.session.add(other)
        db.session.commit()
        inquiry = _make_inquiry(db, user_id=other.id)
        notif = _make_notification(db, other.id, inquiry.id, is_read=False)
        authenticated_client.post('/notifications/mark-read')
        assert db.session.get(InquiryNotification, notif.id).is_read is False


class TestMarkSingleNotificationRead:
    def test_requires_login(self, client):
        response = client.post('/notifications/1/mark-read')
        assert response.status_code in (302, 401, 403)

    def test_marks_own_notification_as_read(self, app, authenticated_client, test_user):
        from app import db
        inquiry = _make_inquiry(db, user_id=test_user.id)
        notif = _make_notification(db, test_user.id, inquiry.id, is_read=False)
        response = authenticated_client.post(f'/notifications/{notif.id}/mark-read')
        assert response.status_code == 200
        assert db.session.get(InquiryNotification, notif.id).is_read is True

    def test_cannot_mark_another_users_notification(self, app, authenticated_client, test_user):
        from app import db
        from models.user import User
        from werkzeug.security import generate_password_hash
        other = User(
            name='Other', email='other2@example.com',
            password=generate_password_hash('Pass123'), email_verified=True,
        )
        db.session.add(other)
        db.session.commit()
        inquiry = _make_inquiry(db, user_id=other.id)
        notif = _make_notification(db, other.id, inquiry.id, is_read=False)
        authenticated_client.post(f'/notifications/{notif.id}/mark-read')
        assert db.session.get(InquiryNotification, notif.id).is_read is False

    def test_already_read_notification_stays_read(self, app, authenticated_client, test_user):
        from app import db
        inquiry = _make_inquiry(db, user_id=test_user.id)
        notif = _make_notification(db, test_user.id, inquiry.id, is_read=True)
        response = authenticated_client.post(f'/notifications/{notif.id}/mark-read')
        assert response.status_code == 200
        assert db.session.get(InquiryNotification, notif.id).is_read is True
