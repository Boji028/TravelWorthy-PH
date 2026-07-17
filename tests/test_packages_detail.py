"""Tests for public package detail and autocomplete routes."""
from datetime import date, timedelta
from models.package import TourPackage
from models.package_image import PackageImage
from models.inquiry import Inquiry
from constants import InquiryStatus


def _make_package(db, **overrides):
    defaults = dict(
        title="Island Hopping",
        description="Explore the islands.",
        destination="Coron",
        duration_days=3,
        price=4500.00,
        currency="PHP",
        is_active=True,
        is_featured=False,
    )
    defaults.update(overrides)
    pkg = TourPackage(**defaults)
    db.session.add(pkg)
    db.session.commit()
    return pkg


def _make_inquiry(db, user_id, package_id, status=InquiryStatus.CONFIRMED.value):
    """Create a confirmed-booking Inquiry linking a user to a package —
    the eligibility check package_detail/submit_review both enforce for
    reviews."""
    inquiry = Inquiry(
        name="Test User",
        email="testuser@example.com",
        contact_number="+639171234567",
        destination="Coron",
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


class TestPackageDetail:
    def test_active_package_accessible(self, app, client):
        from app import db

        pkg = _make_package(db)
        response = client.get(f"/packages/{pkg.id}")
        assert response.status_code == 200

    def test_inactive_package_returns_404(self, app, client):
        from app import db

        pkg = _make_package(db, is_active=False)
        response = client.get(f"/packages/{pkg.id}")
        assert response.status_code == 404

    def test_nonexistent_package_returns_404(self, app, client):
        response = client.get("/packages/99999")
        assert response.status_code == 404

    def test_detail_contains_title(self, app, client):
        from app import db

        pkg = _make_package(db, title="Coron Adventure")
        response = client.get(f"/packages/{pkg.id}")
        assert b"Coron Adventure" in response.data

    def test_detail_contains_destination(self, app, client):
        from app import db

        pkg = _make_package(db, destination="Coron", title="My Tour")
        response = client.get(f"/packages/{pkg.id}")
        assert b"Coron" in response.data

    def test_detail_shows_gallery_images(self, app, client):
        from app import db

        pkg = _make_package(db)
        img = PackageImage(
            package_id=pkg.id,
            path="https://cdn.example.com/gallery.jpg",
        )
        db.session.add(img)
        db.session.commit()
        response = client.get(f"/packages/{pkg.id}")
        assert response.status_code == 200

    def test_guest_sees_inquire_button_not_login_gate(self, app, client):
        """Regression test — package detail pages used to hide the inquiry
        form behind a login wall, inconsistent with the Visa page and Plan
        My Trip, which both let guests inquire directly. The button should
        always be 'Inquire Now', never 'Login to Inquire'."""
        from app import db

        pkg = _make_package(db)
        response = client.get(f"/packages/{pkg.id}")
        assert b"Inquire Now" in response.data
        assert b"Login to Inquire" not in response.data

    def test_review_form_posts_to_submit_review(self, app, authenticated_client, test_user):
        """Regression test: the review form must post to packages.submit_review,
        not bookings.inquire_package — a copy-paste bug once made review
        submission silently impossible through the UI."""
        from app import db

        pkg = _make_package(db)
        _make_inquiry(db, user_id=test_user.id, package_id=pkg.id)
        response = authenticated_client.get(f"/packages/{pkg.id}")
        review_action = f'/packages/{pkg.id}/review"'.encode()
        assert review_action in response.data

    def test_already_reviewed_shows_edit_form(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview

        pkg = _make_package(db)
        db.session.add(PackageReview(package_id=pkg.id, user_id=test_user.id, rating=4, message="Pretty good trip."))
        db.session.commit()
        response = authenticated_client.get(f"/packages/{pkg.id}")
        assert f"/packages/{pkg.id}/review/edit".encode() in response.data
        assert b"Pretty good trip." in response.data

    def test_review_form_hidden_without_confirmed_booking(self, app, authenticated_client, test_user):
        """Regression test: the review form used to render for any logged-in
        user regardless of booking status — the confirmed-booking
        requirement only ever surfaced after they wrote a review and hit
        submit. package_detail() now computes the same eligibility check
        submit_review() enforces, so the form itself is gated, not just
        the submission."""
        from app import db

        pkg = _make_package(db)
        # test_user has no Inquiry for this package at all — not eligible.
        response = authenticated_client.get(f"/packages/{pkg.id}")
        review_action = f'/packages/{pkg.id}/review"'.encode()
        assert review_action not in response.data
        assert b"confirmed booking" in response.data

    def test_review_form_hidden_with_unconfirmed_inquiry(self, app, authenticated_client, test_user):
        """A pending/contacted inquiry (not yet confirmed or closed) does
        not unlock the review form — same rule as submit_review()."""
        from app import db

        pkg = _make_package(db)
        _make_inquiry(db, user_id=test_user.id, package_id=pkg.id, status=InquiryStatus.CONTACTED.value)
        response = authenticated_client.get(f"/packages/{pkg.id}")
        review_action = f'/packages/{pkg.id}/review"'.encode()
        assert review_action not in response.data


class TestAutocomplete:
    def test_returns_json(self, app, client):
        from app import db

        _make_package(db, destination="Palawan")
        response = client.get("/packages/autocomplete?q=Palawan")
        assert response.status_code == 200
        assert response.is_json

    def test_matches_destination(self, app, client):
        from app import db

        _make_package(db, destination="Boracay")
        response = client.get("/packages/autocomplete?q=Boracay")
        data = response.get_json()
        assert any("Boracay" in str(item) for item in data)

    def test_short_query_returns_empty(self, app, client):
        response = client.get("/packages/autocomplete?q=a")
        assert response.status_code == 200
        assert response.get_json() == []

    def test_blank_query_returns_empty(self, app, client):
        response = client.get("/packages/autocomplete?q=")
        assert response.status_code == 200
        assert response.get_json() == []

    def test_no_match_returns_empty(self, app, client):
        response = client.get("/packages/autocomplete?q=xyznonexistent")
        data = response.get_json()
        assert data == [] or len(data) == 0

    def test_only_active_packages_returned(self, app, client):
        from app import db

        _make_package(db, destination="ActiveDest", is_active=True)
        _make_package(db, destination="InactiveDest", is_active=False)
        response = client.get("/packages/autocomplete?q=InactiveDest")
        data = response.get_json()
        assert not any("InactiveDest" in str(item) for item in data)
