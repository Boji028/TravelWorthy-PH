"""Tests for inquiry_cleanup_service: the auto-delete-after-3-months feature.

Covers both halves independently: the expiry-warning notification (with
its throttle and "already downloaded recently" skip) and the actual
deletion (with its cascade to InquiryNotification).
"""
from datetime import datetime, timezone, timedelta
from models.inquiry import Inquiry
from models.inquiry_notification import InquiryNotification


def _make_inquiry(db, created_at, **overrides):
    defaults = dict(
        name="Juan Dela Cruz",
        email="juan@example.com",
        contact_number="09171234567",
        destination="Boracay",
        travel_date_from=datetime.now(timezone.utc).date(),
        travel_date_to=datetime.now(timezone.utc).date(),
        status="new",
    )
    defaults.update(overrides)
    inquiry = Inquiry(**defaults)
    db.session.add(inquiry)
    db.session.commit()
    # created_at has a default, so set it directly after insert
    inquiry.created_at = created_at
    db.session.commit()
    return inquiry


class TestDeleteExpiredInquiries:
    def test_deletes_inquiry_older_than_90_days(self, app, admin_user):
        from app import db
        from inquiry_cleanup_service import delete_expired_inquiries

        old = _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=91))

        deleted = delete_expired_inquiries()

        assert deleted == 1
        assert db.session.get(Inquiry, old.id) is None

    def test_keeps_inquiry_newer_than_90_days_regardless_of_status(self, app, admin_user):
        from app import db
        from inquiry_cleanup_service import delete_expired_inquiries

        recent = _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=10), status="closed")

        deleted = delete_expired_inquiries()

        assert deleted == 0
        assert db.session.get(Inquiry, recent.id) is not None

    def test_deleting_expired_inquiry_cascades_its_notifications(self, app, admin_user):
        from app import db
        from inquiry_cleanup_service import delete_expired_inquiries

        old = _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=95))
        notif = InquiryNotification(user_id=admin_user.id, inquiry_id=old.id, message="New inquiry")
        db.session.add(notif)
        db.session.commit()
        notif_id = notif.id

        delete_expired_inquiries()

        assert db.session.get(InquiryNotification, notif_id) is None


class TestNotifyAdminsOfExpiringInquiries:
    def test_sends_reminder_for_inquiry_in_final_week_not_recently_exported(self, app, admin_user):
        from app import db
        from inquiry_cleanup_service import notify_admins_of_expiring_inquiries

        _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=85))  # 5 days from deletion

        at_risk = notify_admins_of_expiring_inquiries()

        assert at_risk == 1
        notif = InquiryNotification.query.filter_by(user_id=admin_user.id, inquiry_id=None).first()
        assert notif is not None
        assert "1 inquiry" in notif.message

    def test_skips_inquiry_exported_within_the_last_week(self, app, admin_user):
        from app import db
        from inquiry_cleanup_service import notify_admins_of_expiring_inquiries

        inquiry = _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=85))
        inquiry.last_exported_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.session.commit()

        at_risk = notify_admins_of_expiring_inquiries()

        assert at_risk == 0
        assert InquiryNotification.query.filter_by(inquiry_id=None).count() == 0

    def test_ignores_inquiries_outside_the_warning_window(self, app, admin_user):
        from app import db
        from inquiry_cleanup_service import notify_admins_of_expiring_inquiries

        _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=30))  # far from deletion

        at_risk = notify_admins_of_expiring_inquiries()

        assert at_risk == 0

    def test_throttles_repeated_calls(self, app, admin_user):
        from app import db
        from inquiry_cleanup_service import notify_admins_of_expiring_inquiries

        _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=85))

        first = notify_admins_of_expiring_inquiries()
        second = notify_admins_of_expiring_inquiries()

        assert first == 1
        assert second == 0
        assert InquiryNotification.query.filter_by(inquiry_id=None).count() == 1


class TestExportStampsLastExportedAt:
    def test_export_route_stamps_last_exported_at(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db, datetime.now(timezone.utc) - timedelta(days=1))
        assert inquiry.last_exported_at is None

        response = admin_client.get("/admin/inquiries/export")
        assert response.status_code == 200

        db.session.refresh(inquiry)
        assert inquiry.last_exported_at is not None


class TestNotificationDropdownHandlesSystemNotifications:
    def test_admin_dashboard_renders_with_a_system_wide_notification(self, app, admin_user, admin_client):
        from app import db

        notif = InquiryNotification(user_id=admin_user.id, inquiry_id=None, message="3 inquiries will be auto-deleted soon.")
        db.session.add(notif)
        db.session.commit()

        response = admin_client.get("/admin/")
        assert response.status_code == 200
        assert b"will be auto-deleted soon" in response.data
