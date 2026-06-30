"""Tests for admin continent and country delete routes."""
from models.continent import Continent
from models.country import Country
from models.package import TourPackage


def _make_continent(db, **overrides):
    defaults = dict(name='Asia', is_active=True)
    defaults.update(overrides)
    c = Continent(**defaults)
    db.session.add(c)
    db.session.commit()
    return c


def _make_country(db, continent_id=None, **overrides):
    defaults = dict(name='Philippines', is_active=True, continent_id=continent_id)
    defaults.update(overrides)
    c = Country(**defaults)
    db.session.add(c)
    db.session.commit()
    return c


def _make_package(db, country_id=None):
    pkg = TourPackage(
        title='Tour',
        description='A tour',
        destination='Somewhere',
        duration_days=5,
        price=5000.00,
        currency='PHP',
        is_active=True,
        country_id=country_id,
    )
    db.session.add(pkg)
    db.session.commit()
    return pkg


class TestDeleteContinent:
    def test_requires_login(self, client):
        response = client.post('/admin/continents/delete/1')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        continent = _make_continent(db)
        authenticated_client.post(f'/admin/continents/delete/{continent.id}')
        assert db.session.get(Continent, continent.id) is not None

    def test_admin_can_delete_empty_continent(self, app, admin_client):
        from app import db
        continent = _make_continent(db)
        continent_id = continent.id
        response = admin_client.post(f'/admin/continents/delete/{continent_id}')
        assert response.status_code == 302
        assert db.session.get(Continent, continent_id) is None

    def test_blocked_when_countries_exist(self, app, admin_client):
        from app import db
        continent = _make_continent(db)
        _make_country(db, continent_id=continent.id)
        continent_id = continent.id
        admin_client.post(f'/admin/continents/delete/{continent_id}')
        assert db.session.get(Continent, continent_id) is not None

    def test_nonexistent_continent_returns_404(self, app, admin_client):
        response = admin_client.post('/admin/continents/delete/99999')
        assert response.status_code == 404


class TestDeleteCountry:
    def test_requires_login(self, client):
        response = client.post('/admin/countries/delete/1')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        country = _make_country(db)
        authenticated_client.post(f'/admin/countries/delete/{country.id}')
        assert db.session.get(Country, country.id) is not None

    def test_admin_can_delete_empty_country(self, app, admin_client):
        from app import db
        country = _make_country(db)
        country_id = country.id
        response = admin_client.post(f'/admin/countries/delete/{country_id}')
        assert response.status_code == 302
        assert db.session.get(Country, country_id) is None

    def test_blocked_when_packages_exist(self, app, admin_client):
        from app import db
        country = _make_country(db)
        _make_package(db, country_id=country.id)
        country_id = country.id
        admin_client.post(f'/admin/countries/delete/{country_id}')
        assert db.session.get(Country, country_id) is not None

    def test_nonexistent_country_returns_404(self, app, admin_client):
        response = admin_client.post('/admin/countries/delete/99999')
        assert response.status_code == 404
