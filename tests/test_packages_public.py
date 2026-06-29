"""Tests for the public packages list page's domestic/international filter.

This route (routes/packages.py::list_packages) had zero test coverage
before this file — it's exercised manually in the browser but nothing
in the suite would have caught a regression in the package_type query
param handling.
"""
from models.package import TourPackage


def _make_package(db, **overrides):
    defaults = dict(
        title='Test Package',
        description='A test tour package',
        destination='Test Destination',
        duration_days=5,
        price=10000.00,
        currency='PHP',
        is_active=True,
        package_type='domestic',
    )
    defaults.update(overrides)
    package = TourPackage(**defaults)
    db.session.add(package)
    db.session.commit()
    return package


class TestPackageTypeFilter:
    def test_no_filter_returns_both_types(self, app, client):
        from app import db
        _make_package(db, title='Boracay Getaway', package_type='domestic')
        _make_package(db, title='Tokyo Adventure', package_type='international')

        response = client.get('/packages/')
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'Boracay Getaway' in page
        assert 'Tokyo Adventure' in page

    def test_domestic_filter_excludes_international(self, app, client):
        from app import db
        _make_package(db, title='Boracay Getaway', package_type='domestic')
        _make_package(db, title='Tokyo Adventure', package_type='international')

        response = client.get('/packages/?package_type=domestic')
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'Boracay Getaway' in page
        assert 'Tokyo Adventure' not in page

    def test_international_filter_excludes_domestic(self, app, client):
        from app import db
        _make_package(db, title='Boracay Getaway', package_type='domestic')
        _make_package(db, title='Tokyo Adventure', package_type='international')

        response = client.get('/packages/?package_type=international')
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'Tokyo Adventure' in page
        assert 'Boracay Getaway' not in page

    def test_invalid_package_type_value_is_ignored(self, app, client):
        """package_type values other than 'domestic'/'international' should
        fall through to no filtering at all, not raise or return nothing."""
        from app import db
        _make_package(db, title='Boracay Getaway', package_type='domestic')
        _make_package(db, title='Tokyo Adventure', package_type='international')

        response = client.get('/packages/?package_type=garbage')
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'Boracay Getaway' in page
        assert 'Tokyo Adventure' in page

    def test_inactive_package_excluded_regardless_of_type(self, app, client):
        from app import db
        _make_package(db, title='Hidden Tour', package_type='domestic', is_active=False)

        response = client.get('/packages/?package_type=domestic')
        assert response.status_code == 200
        assert 'Hidden Tour' not in response.get_data(as_text=True)

    def test_ajax_request_returns_partial_template(self, app, client):
        """X-Requested-With triggers the list_ajax.html partial instead of
        the full page — confirm it still respects the filter and doesn't
        error out on missing full-page context vars."""
        from app import db
        _make_package(db, title='Boracay Getaway', package_type='domestic')
        _make_package(db, title='Tokyo Adventure', package_type='international')

        response = client.get(
            '/packages/?package_type=domestic',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'Boracay Getaway' in page
        assert 'Tokyo Adventure' not in page

    def test_combining_package_type_with_destination_search(self, app, client):
        from app import db
        _make_package(db, title='Boracay Getaway', destination='Boracay', package_type='domestic')
        _make_package(db, title='Palawan Escape', destination='Palawan', package_type='domestic')

        response = client.get('/packages/?package_type=domestic&destination=Boracay')
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'Boracay Getaway' in page
        assert 'Palawan Escape' not in page
