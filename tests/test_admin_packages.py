"""Tests for admin package management routes (toggles, bulk actions, delete)."""
from datetime import date, timedelta
from models.package import TourPackage
from models.inquiry import Inquiry


def _make_package(db, **overrides):
    defaults = dict(
        title='Test Package',
        description='A test tour package',
        destination='Palawan',
        duration_days=5,
        price=9999.00,
        currency='PHP',
        is_active=True,
        is_featured=False,
    )
    defaults.update(overrides)
    pkg = TourPackage(**defaults)
    db.session.add(pkg)
    db.session.commit()
    return pkg


def _make_inquiry(db, package_id, status='new'):
    today = date.today()
    inquiry = Inquiry(
        name='Customer',
        email='customer@example.com',
        contact_number='+639171234567',
        destination='Palawan',
        travel_date_from=today + timedelta(days=10),
        travel_date_to=today + timedelta(days=14),
        num_adults=2,
        package_id=package_id,
        status=status,
    )
    db.session.add(inquiry)
    db.session.commit()
    return inquiry


class TestTogglePackageActive:
    def test_requires_login(self, client):
        response = client.post('/admin/packages/toggle-active/1')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        pkg = _make_package(db)
        authenticated_client.post(f'/admin/packages/toggle-active/{pkg.id}')
        assert db.session.get(TourPackage, pkg.id).is_active is True

    def test_flips_active_to_inactive(self, app, admin_client):
        from app import db
        pkg = _make_package(db, is_active=True)
        response = admin_client.post(f'/admin/packages/toggle-active/{pkg.id}')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['is_active'] is False
        assert db.session.get(TourPackage, pkg.id).is_active is False

    def test_flips_inactive_to_active(self, app, admin_client):
        from app import db
        pkg = _make_package(db, is_active=False)
        admin_client.post(f'/admin/packages/toggle-active/{pkg.id}')
        assert db.session.get(TourPackage, pkg.id).is_active is True

    def test_toggle_twice_restores_original_state(self, app, admin_client):
        from app import db
        pkg = _make_package(db, is_active=True)
        admin_client.post(f'/admin/packages/toggle-active/{pkg.id}')
        admin_client.post(f'/admin/packages/toggle-active/{pkg.id}')
        assert db.session.get(TourPackage, pkg.id).is_active is True

    def test_nonexistent_package_returns_404(self, app, admin_client):
        response = admin_client.post('/admin/packages/toggle-active/99999')
        assert response.status_code == 404


class TestTogglePackageFeatured:
    def test_requires_login(self, client):
        response = client.post('/admin/packages/toggle-featured/1')
        assert response.status_code in (302, 401, 403)

    def test_flips_featured_state(self, app, admin_client):
        from app import db
        pkg = _make_package(db, is_featured=False)
        response = admin_client.post(f'/admin/packages/toggle-featured/{pkg.id}')
        assert response.status_code == 200
        assert response.json['is_featured'] is True
        assert db.session.get(TourPackage, pkg.id).is_featured is True

    def test_toggle_twice_restores_original(self, app, admin_client):
        from app import db
        pkg = _make_package(db, is_featured=True)
        admin_client.post(f'/admin/packages/toggle-featured/{pkg.id}')
        admin_client.post(f'/admin/packages/toggle-featured/{pkg.id}')
        assert db.session.get(TourPackage, pkg.id).is_featured is True


class TestBulkPackageAction:
    def test_requires_login(self, client):
        response = client.post('/admin/packages/bulk-action', data={'action': 'activate'})
        assert response.status_code in (302, 401, 403)

    def test_no_packages_selected_redirects(self, app, admin_client):
        response = admin_client.post(
            '/admin/packages/bulk-action',
            data={'action': 'activate'},
            follow_redirects=False,
        )
        assert response.status_code == 302

    def test_activate_sets_packages_active(self, app, admin_client):
        from app import db
        p1 = _make_package(db, is_active=False, title='P1')
        p2 = _make_package(db, is_active=False, title='P2')
        admin_client.post('/admin/packages/bulk-action', data={
            'action': 'activate',
            'package_ids': [p1.id, p2.id],
        })
        assert db.session.get(TourPackage, p1.id).is_active is True
        assert db.session.get(TourPackage, p2.id).is_active is True

    def test_deactivate_sets_packages_inactive(self, app, admin_client):
        from app import db
        p1 = _make_package(db, is_active=True, title='P1')
        p2 = _make_package(db, is_active=True, title='P2')
        admin_client.post('/admin/packages/bulk-action', data={
            'action': 'deactivate',
            'package_ids': [p1.id, p2.id],
        })
        assert db.session.get(TourPackage, p1.id).is_active is False
        assert db.session.get(TourPackage, p2.id).is_active is False

    def test_delete_removes_packages(self, app, admin_client):
        from app import db
        p1 = _make_package(db, title='P1')
        p2 = _make_package(db, title='P2')
        admin_client.post('/admin/packages/bulk-action', data={
            'action': 'delete',
            'package_ids': [p1.id, p2.id],
        })
        assert db.session.get(TourPackage, p1.id) is None
        assert db.session.get(TourPackage, p2.id) is None

    def test_delete_skips_packages_with_open_inquiries(self, app, admin_client):
        from app import db
        blocked = _make_package(db, title='Blocked')
        safe = _make_package(db, title='Safe')
        _make_inquiry(db, package_id=blocked.id, status='new')
        admin_client.post('/admin/packages/bulk-action', data={
            'action': 'delete',
            'package_ids': [blocked.id, safe.id],
        })
        assert db.session.get(TourPackage, blocked.id) is not None
        assert db.session.get(TourPackage, safe.id) is None

    def test_delete_allows_package_with_only_closed_inquiries(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        _make_inquiry(db, package_id=pkg.id, status='closed')
        pkg_id = pkg.id
        admin_client.post('/admin/packages/bulk-action', data={
            'action': 'delete',
            'package_ids': [pkg_id],
        })
        assert db.session.get(TourPackage, pkg_id) is None

    def test_invalid_action_redirects_without_change(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        admin_client.post('/admin/packages/bulk-action', data={
            'action': 'explode',
            'package_ids': [pkg.id],
        })
        assert db.session.get(TourPackage, pkg.id) is not None


class TestPackageReviewSubmit:
    def test_requires_login(self, app, client):
        from app import db
        pkg = _make_package(db)
        response = client.post(f'/packages/{pkg.id}/review', data={
            'rating': '5',
            'message': 'Great tour!',
        })
        assert response.status_code in (302, 401, 403)

    def _make_confirmed_inquiry(self, db, pkg, user):
        today = date.today()
        inq = Inquiry(
            name=user.name, email=user.email,
            contact_number='+639171234567',
            destination='Palawan',
            travel_date_from=today + timedelta(days=10),
            travel_date_to=today + timedelta(days=14),
            num_adults=2,
            package_id=pkg.id,
            user_id=user.id,
            status='confirmed',
        )
        db.session.add(inq)
        db.session.commit()
        return inq

    def test_valid_review_is_saved(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        self._make_confirmed_inquiry(db, pkg, test_user)
        authenticated_client.post(f'/packages/{pkg.id}/review', data={
            'rating': '4',
            'message': 'Really enjoyed it.',
        })
        assert PackageReview.query.filter_by(package_id=pkg.id).count() == 1

    def test_duplicate_review_is_blocked(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        self._make_confirmed_inquiry(db, pkg, test_user)
        authenticated_client.post(f'/packages/{pkg.id}/review', data={
            'rating': '5', 'message': 'First review.',
        })
        authenticated_client.post(f'/packages/{pkg.id}/review', data={
            'rating': '3', 'message': 'Second review.',
        })
        assert PackageReview.query.filter_by(package_id=pkg.id).count() == 1

    def test_no_booking_blocks_review(self, app, authenticated_client):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        response = authenticated_client.post(f'/packages/{pkg.id}/review', data={
            'rating': '5', 'message': 'Great!',
        }, follow_redirects=True)
        assert PackageReview.query.count() == 0

    def test_empty_message_does_not_save(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        self._make_confirmed_inquiry(db, pkg, test_user)
        authenticated_client.post(f'/packages/{pkg.id}/review', data={
            'rating': '5', 'message': '',
        })
        assert PackageReview.query.count() == 0

    def test_invalid_rating_is_rejected(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        self._make_confirmed_inquiry(db, pkg, test_user)
        authenticated_client.post(f'/packages/{pkg.id}/review', data={
            'rating': '99', 'message': 'Good.',
        })
        assert PackageReview.query.count() == 0

    def test_inactive_package_returns_404(self, app, authenticated_client):
        from app import db
        pkg = _make_package(db, is_active=False)
        response = authenticated_client.post(f'/packages/{pkg.id}/review', data={
            'rating': '5', 'message': 'Should not work.',
        })
        assert response.status_code == 404


class TestPackageReviewEdit:
    def test_requires_login(self, app, client):
        from app import db
        pkg = _make_package(db)
        response = client.post(f'/packages/{pkg.id}/review/edit', data={
            'rating': '5', 'message': 'Updated.',
        })
        assert response.status_code in (302, 401, 403)

    def test_no_existing_review_returns_404(self, app, authenticated_client):
        from app import db
        pkg = _make_package(db)
        response = authenticated_client.post(f'/packages/{pkg.id}/review/edit', data={
            'rating': '5', 'message': 'Updated.',
        })
        assert response.status_code == 404

    def test_updates_existing_review(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        review = PackageReview(package_id=pkg.id, user_id=test_user.id, rating=3, message='Okay trip.')
        db.session.add(review)
        db.session.commit()
        authenticated_client.post(f'/packages/{pkg.id}/review/edit', data={
            'rating': '5', 'message': 'Actually it was great!',
        })
        updated = db.session.get(PackageReview, review.id)
        assert updated.rating == 5
        assert updated.message == 'Actually it was great!'
        assert PackageReview.query.filter_by(package_id=pkg.id).count() == 1

    def test_invalid_rating_does_not_change_review(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        review = PackageReview(package_id=pkg.id, user_id=test_user.id, rating=3, message='Okay trip.')
        db.session.add(review)
        db.session.commit()
        authenticated_client.post(f'/packages/{pkg.id}/review/edit', data={
            'rating': '99', 'message': 'Should not save.',
        })
        updated = db.session.get(PackageReview, review.id)
        assert updated.rating == 3
        assert updated.message == 'Okay trip.'

    def test_empty_message_does_not_change_review(self, app, authenticated_client, test_user):
        from app import db
        from models.package_review import PackageReview
        pkg = _make_package(db)
        review = PackageReview(package_id=pkg.id, user_id=test_user.id, rating=3, message='Okay trip.')
        db.session.add(review)
        db.session.commit()
        authenticated_client.post(f'/packages/{pkg.id}/review/edit', data={
            'rating': '5', 'message': '',
        })
        updated = db.session.get(PackageReview, review.id)
        assert updated.message == 'Okay trip.'
