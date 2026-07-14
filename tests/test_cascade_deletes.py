"""Regression tests for a class of cascade-delete bugs.

Root cause: several db.relationship() backrefs pointed at NOT NULL foreign
keys with no cascade configured. SQLAlchemy's default behavior on parent
delete is to try to null out the child's FK column (not delete the child),
which crashes with a NotNullViolation/IntegrityError whenever that FK is
NOT NULL — regardless of any ondelete='CASCADE' set at the DB level, since
that only takes effect if the relationship uses passive_deletes=True.

This was first caught live in production deleting an Inquiry that had an
InquiryNotification attached (see models/inquiry_notification.py). Auditing
every other backref in models/ for the same pattern turned up two more
live landmines, both now fixed the same way (cascade='all, delete-orphan'
on the parent-side relationship/backref):
  - TourPackage.images  (models/package.py)
  - TourPackage.reviews / User.package_reviews  (models/package_review.py)

Each class below proves: (1) the crash existed before the fix [documented
in comments, not re-triggered here], and (2) the delete now actually
removes the dependent rows instead of merely not crashing.
"""
from datetime import date, timedelta
from models.inquiry import Inquiry
from models.inquiry_notification import InquiryNotification
from models.package import TourPackage
from models.package_image import PackageImage
from models.package_review import PackageReview
from models.user import User
from werkzeug.security import generate_password_hash


def _make_inquiry(db, **overrides):
    today = date.today()
    defaults = dict(
        name="Maria Santos",
        email="maria@example.com",
        contact_number="09171234567",
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


def _make_package(db, **overrides):
    defaults = dict(
        title="Test Package",
        description="A test tour package",
        destination="Test Destination",
        duration_days=5,
        price=10000.00,
        currency="PHP",
        is_active=True,
    )
    defaults.update(overrides)
    package = TourPackage(**defaults)
    db.session.add(package)
    db.session.commit()
    return package


def _make_reviewer(db, **overrides):
    defaults = dict(
        name="Reviewer",
        email="reviewer@example.com",
        password=generate_password_hash("TestPass123"),
        is_admin=False,
        email_verified=True,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db.session.add(user)
    db.session.commit()
    return user


class TestInquiryDeleteWithNotifications:
    """The exact bug reported in production: deleting an inquiry that has
    an InquiryNotification attached used to 500 with a NotNullViolation
    instead of deleting cleanly."""

    def test_delete_inquiry_requires_login(self, client):
        response = client.post("/admin/inquiries/delete/1")
        assert response.status_code in (302, 401, 403)

    def test_delete_inquiry_rejects_non_admin(self, app, authenticated_client):
        from app import db

        inquiry = _make_inquiry(db)
        response = authenticated_client.post(f"/admin/inquiries/delete/{inquiry.id}")
        assert response.status_code in (302, 403)

    def test_delete_inquiry_with_no_notifications(self, app, admin_client):
        from app import db

        inquiry = _make_inquiry(db)
        inquiry_id = inquiry.id
        response = admin_client.post(f"/admin/inquiries/delete/{inquiry_id}")
        assert response.status_code == 302
        assert db.session.get(Inquiry, inquiry_id) is None

    def test_delete_inquiry_with_notification_does_not_500(self, app, admin_client):
        """This is the actual production crash. Before the fix this raised
        IntegrityError -> sqlalchemy.exc.IntegrityError -> Flask 500."""
        from app import db

        reviewer = _make_reviewer(db)
        inquiry = _make_inquiry(db, user_id=reviewer.id)
        inquiry_id = inquiry.id
        notif = InquiryNotification(
            user_id=reviewer.id, inquiry_id=inquiry.id, message="We received your inquiry. We'll be in touch soon!"
        )
        db.session.add(notif)
        db.session.commit()

        response = admin_client.post(f"/admin/inquiries/delete/{inquiry_id}")
        assert response.status_code == 302
        assert db.session.get(Inquiry, inquiry_id) is None
        assert InquiryNotification.query.filter_by(inquiry_id=inquiry_id).count() == 0

    def test_delete_inquiry_with_multiple_notifications(self, app, admin_client):
        """The production log showed two notification rows (ids 18, 19)
        attached to one inquiry — confirm that case specifically."""
        from app import db

        reviewer = _make_reviewer(db)
        inquiry = _make_inquiry(db, user_id=reviewer.id)
        inquiry_id = inquiry.id
        db.session.add_all(
            [
                InquiryNotification(user_id=reviewer.id, inquiry_id=inquiry.id, message="First"),
                InquiryNotification(user_id=reviewer.id, inquiry_id=inquiry.id, message="Second"),
            ]
        )
        db.session.commit()

        response = admin_client.post(f"/admin/inquiries/delete/{inquiry_id}")
        assert response.status_code == 302
        assert InquiryNotification.query.count() == 0


class TestPackageDeleteWithImagesAndReviews:
    """Same root cause, different table: TourPackage.images and
    TourPackage.reviews both had NOT NULL FKs with no cascade — deleting a
    package that had either would 500 the same way."""

    def test_delete_package_with_no_images_or_reviews(self, app, admin_client):
        from app import db

        package = _make_package(db)
        package_id = package.id
        response = admin_client.post(f"/admin/packages/delete/{package_id}")
        assert response.status_code == 302
        assert db.session.get(TourPackage, package_id) is None

    def test_delete_package_with_gallery_image_does_not_500(self, app, admin_client):
        from app import db

        package = _make_package(db)
        package_id = package.id
        db.session.add(PackageImage(package_id=package.id, path="gallery1.jpg", order=0))
        db.session.commit()

        response = admin_client.post(f"/admin/packages/delete/{package_id}")
        assert response.status_code == 302
        assert db.session.get(TourPackage, package_id) is None
        assert PackageImage.query.filter_by(package_id=package_id).count() == 0

    def test_delete_package_with_review_does_not_500(self, app, admin_client):
        from app import db

        reviewer = _make_reviewer(db)
        package = _make_package(db)
        package_id = package.id
        db.session.add(PackageReview(package_id=package.id, user_id=reviewer.id, rating=5, message="Loved it!"))
        db.session.commit()

        response = admin_client.post(f"/admin/packages/delete/{package_id}")
        assert response.status_code == 302
        assert db.session.get(TourPackage, package_id) is None
        assert PackageReview.query.filter_by(package_id=package_id).count() == 0


class TestUserDeleteWithPackageReviews:
    """User.package_reviews had the same NOT NULL FK + no-cascade gap. The
    delete_user route's own comment claimed the DB-level ondelete='CASCADE'
    handled this — it didn't, because SQLAlchemy manages relationships at
    the ORM level before that constraint ever gets a chance to fire."""

    def test_delete_user_with_no_reviews(self, app, admin_client):
        from app import db

        user = _make_reviewer(db, email="plain@example.com")
        user_id = user.id
        response = admin_client.post(f"/admin/users/delete/{user_id}")
        assert response.status_code == 302
        assert db.session.get(User, user_id) is None

    def test_delete_user_with_package_review_does_not_500(self, app, admin_client):
        from app import db

        reviewer = _make_reviewer(db, email="hasreview@example.com")
        user_id = reviewer.id
        package = _make_package(db)
        db.session.add(PackageReview(package_id=package.id, user_id=reviewer.id, rating=4, message="Pretty good"))
        db.session.commit()

        response = admin_client.post(f"/admin/users/delete/{user_id}")
        assert response.status_code == 302
        assert db.session.get(User, user_id) is None
        assert PackageReview.query.filter_by(user_id=user_id).count() == 0


class TestUserDeleteWithAuthTokens:
    """Same NOT NULL FK + no-cascade gap on the two auth token tables.
    PasswordResetToken was a live landmine: delete_user manually cleaned up
    EmailVerificationToken and InquiryNotification rows but never
    PasswordResetToken, so deleting any user who had ever requested a
    password reset raised IntegrityError -> 500."""

    def test_delete_user_with_password_reset_token_does_not_500(self, app, admin_client):
        from app import db
        from models.password_reset import PasswordResetToken

        user = _make_reviewer(db, email="forgotpass@example.com")
        user_id = user.id
        db.session.add(PasswordResetToken.generate_token(user_id))
        db.session.commit()

        response = admin_client.post(f"/admin/users/delete/{user_id}")
        assert response.status_code == 302
        assert db.session.get(User, user_id) is None
        assert PasswordResetToken.query.filter_by(user_id=user_id).count() == 0

    def test_delete_user_with_verification_token_does_not_500(self, app, admin_client):
        from app import db
        from models.email_verification import EmailVerificationToken

        user = _make_reviewer(db, email="unverified@example.com", email_verified=False)
        user_id = user.id
        db.session.add(EmailVerificationToken.generate_token(user_id, user.email))
        db.session.commit()

        response = admin_client.post(f"/admin/users/delete/{user_id}")
        assert response.status_code == 302
        assert db.session.get(User, user_id) is None
        assert EmailVerificationToken.query.filter_by(user_id=user_id).count() == 0
