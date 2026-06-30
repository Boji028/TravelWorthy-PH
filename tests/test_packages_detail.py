"""Tests for public package detail and autocomplete routes."""
from models.package import TourPackage
from models.package_image import PackageImage


def _make_package(db, **overrides):
    defaults = dict(
        title='Island Hopping',
        description='Explore the islands.',
        destination='Coron',
        duration_days=3,
        price=4500.00,
        currency='PHP',
        is_active=True,
        is_featured=False,
    )
    defaults.update(overrides)
    pkg = TourPackage(**defaults)
    db.session.add(pkg)
    db.session.commit()
    return pkg


class TestPackageDetail:
    def test_active_package_accessible(self, app, client):
        from app import db
        pkg = _make_package(db)
        response = client.get(f'/packages/{pkg.id}')
        assert response.status_code == 200

    def test_inactive_package_returns_404(self, app, client):
        from app import db
        pkg = _make_package(db, is_active=False)
        response = client.get(f'/packages/{pkg.id}')
        assert response.status_code == 404

    def test_nonexistent_package_returns_404(self, app, client):
        response = client.get('/packages/99999')
        assert response.status_code == 404

    def test_detail_contains_title(self, app, client):
        from app import db
        pkg = _make_package(db, title='Coron Adventure')
        response = client.get(f'/packages/{pkg.id}')
        assert b'Coron Adventure' in response.data

    def test_detail_contains_destination(self, app, client):
        from app import db
        pkg = _make_package(db, destination='Coron', title='My Tour')
        response = client.get(f'/packages/{pkg.id}')
        assert b'Coron' in response.data

    def test_detail_shows_gallery_images(self, app, client):
        from app import db
        pkg = _make_package(db)
        img = PackageImage(
            package_id=pkg.id,
            path='https://cdn.example.com/gallery.jpg',
        )
        db.session.add(img)
        db.session.commit()
        response = client.get(f'/packages/{pkg.id}')
        assert response.status_code == 200

    def test_review_form_posts_to_submit_review(self, app, authenticated_client):
        """Regression test: the review form must post to packages.submit_review,
        not bookings.inquire_package — a copy-paste bug once made review
        submission silently impossible through the UI."""
        from app import db
        pkg = _make_package(db)
        response = authenticated_client.get(f'/packages/{pkg.id}')
        review_action = f'/packages/{pkg.id}/review"'.encode()
        assert review_action in response.data

    def test_already_reviewed_shows_edit_form(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        db.session.add(PackageReview(
            package_id=pkg.id, user_id=test_user.id, rating=4, message='Pretty good trip.'
        ))
        db.session.commit()
        response = authenticated_client.get(f'/packages/{pkg.id}')
        assert f'/packages/{pkg.id}/review/edit'.encode() in response.data
        assert b'Pretty good trip.' in response.data


class TestAutocomplete:
    def test_returns_json(self, app, client):
        from app import db
        _make_package(db, destination='Palawan')
        response = client.get('/packages/autocomplete?q=Palawan')
        assert response.status_code == 200
        assert response.is_json

    def test_matches_destination(self, app, client):
        from app import db
        _make_package(db, destination='Boracay')
        response = client.get('/packages/autocomplete?q=Boracay')
        data = response.get_json()
        assert any('Boracay' in str(item) for item in data)

    def test_short_query_returns_empty(self, app, client):
        response = client.get('/packages/autocomplete?q=a')
        assert response.status_code == 200
        assert response.get_json() == []

    def test_blank_query_returns_empty(self, app, client):
        response = client.get('/packages/autocomplete?q=')
        assert response.status_code == 200
        assert response.get_json() == []

    def test_no_match_returns_empty(self, app, client):
        response = client.get('/packages/autocomplete?q=xyznonexistent')
        data = response.get_json()
        assert data == [] or len(data) == 0

    def test_only_active_packages_returned(self, app, client):
        from app import db
        _make_package(db, destination='ActiveDest', is_active=True)
        _make_package(db, destination='InactiveDest', is_active=False)
        response = client.get('/packages/autocomplete?q=InactiveDest')
        data = response.get_json()
        assert not any('InactiveDest' in str(item) for item in data)
