"""Tests for admin continent and country add/edit routes."""
from unittest.mock import patch
from datetime import datetime, timezone
from io import BytesIO
from models.continent import Continent
from models.country import Country


FAKE_UPLOAD = {
    "path": "https://res.cloudinary.com/test/image/upload/v1/geo.jpg",
    "size_kb": 60.0,
    "uploaded_at": datetime.now(timezone.utc),
}


def _make_continent(db, **overrides):
    defaults = dict(name="Asia", is_active=True)
    defaults.update(overrides)
    c = Continent(**defaults)
    db.session.add(c)
    db.session.commit()
    return c


def _make_country(db, **overrides):
    defaults = dict(name="Philippines", is_active=True)
    defaults.update(overrides)
    c = Country(**defaults)
    db.session.add(c)
    db.session.commit()
    return c


class TestAddContinent:
    def test_requires_login(self, client):
        response = client.post("/admin/continents/add", data={"name": "Asia"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        authenticated_client.post("/admin/continents/add", data={"name": "Asia"})
        assert Continent.query.count() == 0

    def test_get_renders_form(self, app, admin_client):
        response = admin_client.get("/admin/continents/add")
        assert response.status_code == 200

    def test_valid_post_creates_continent(self, app, admin_client):
        from app import db

        admin_client.post("/admin/continents/add", data={"name": "Europe", "is_active": "on"})
        assert Continent.query.filter_by(name="Europe").count() == 1

    def test_missing_name_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/continents/add", data={"name": ""})
        assert Continent.query.count() == 0

    def test_image_upload_sets_url(self, app, admin_client):
        from app import db

        with patch("image_service.ImageUploadService.upload_and_compress", return_value=FAKE_UPLOAD):
            admin_client.post(
                "/admin/continents/add",
                data={"name": "Africa", "image": (BytesIO(b"img"), "africa.jpg")},
                content_type="multipart/form-data",
            )
        continent = Continent.query.filter_by(name="Africa").first()
        assert continent is not None
        assert continent.image == FAKE_UPLOAD["path"]

    def test_redirects_to_continents_list(self, app, admin_client):
        response = admin_client.post(
            "/admin/continents/add",
            data={"name": "Oceania"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin/continents" in response.headers["Location"]


class TestEditContinent:
    def test_requires_login(self, app, client):
        from app import db

        continent = _make_continent(db)
        response = client.post(f"/admin/continents/edit/{continent.id}", data={"name": "X"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        continent = _make_continent(db)
        authenticated_client.post(f"/admin/continents/edit/{continent.id}", data={"name": "Hacked"})
        assert db.session.get(Continent, continent.id).name == "Asia"

    def test_get_renders_form(self, app, admin_client):
        from app import db

        continent = _make_continent(db)
        response = admin_client.get(f"/admin/continents/edit/{continent.id}")
        assert response.status_code == 200

    def test_valid_post_updates_continent(self, app, admin_client):
        from app import db

        continent = _make_continent(db)
        admin_client.post(f"/admin/continents/edit/{continent.id}", data={"name": "East Asia"})
        assert db.session.get(Continent, continent.id).name == "East Asia"

    def test_nonexistent_continent_returns_404(self, app, admin_client):
        response = admin_client.get("/admin/continents/edit/99999")
        assert response.status_code == 404


class TestAddCountry:
    def test_requires_login(self, client):
        response = client.post("/admin/countries/add", data={"name": "Japan"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        authenticated_client.post("/admin/countries/add", data={"name": "Japan"})
        assert Country.query.count() == 0

    def test_get_renders_form(self, app, admin_client):
        response = admin_client.get("/admin/countries/add")
        assert response.status_code == 200

    def test_valid_post_creates_country(self, app, admin_client):
        from app import db

        admin_client.post("/admin/countries/add", data={"name": "Japan", "is_active": "on"})
        assert Country.query.filter_by(name="Japan").count() == 1

    def test_missing_name_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/countries/add", data={"name": ""})
        assert Country.query.count() == 0

    def test_image_upload_sets_url(self, app, admin_client):
        from app import db

        with patch("image_service.ImageUploadService.upload_and_compress", return_value=FAKE_UPLOAD):
            admin_client.post(
                "/admin/countries/add",
                data={"name": "South Korea", "image": (BytesIO(b"img"), "kr.jpg")},
                content_type="multipart/form-data",
            )
        country = Country.query.filter_by(name="South Korea").first()
        assert country is not None
        assert country.image == FAKE_UPLOAD["path"]


class TestEditCountry:
    def test_requires_login(self, app, client):
        from app import db

        country = _make_country(db)
        response = client.post(f"/admin/countries/edit/{country.id}", data={"name": "X"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        country = _make_country(db)
        authenticated_client.post(f"/admin/countries/edit/{country.id}", data={"name": "Hacked"})
        assert db.session.get(Country, country.id).name == "Philippines"

    def test_get_renders_form(self, app, admin_client):
        from app import db

        country = _make_country(db)
        response = admin_client.get(f"/admin/countries/edit/{country.id}")
        assert response.status_code == 200

    def test_valid_post_updates_country(self, app, admin_client):
        from app import db

        country = _make_country(db)
        admin_client.post(f"/admin/countries/edit/{country.id}", data={"name": "Filipino Islands"})
        assert db.session.get(Country, country.id).name == "Filipino Islands"

    def test_field_changes_saved_even_when_no_image(self, app, admin_client):
        from app import db

        country = _make_country(db)
        admin_client.post(
            f"/admin/countries/edit/{country.id}",
            data={"name": "Updated PH", "is_active": "on"},
        )
        updated = db.session.get(Country, country.id)
        assert updated.name == "Updated PH"
        assert updated.is_active is True

    def test_nonexistent_country_returns_404(self, app, admin_client):
        response = admin_client.get("/admin/countries/edit/99999")
        assert response.status_code == 404
