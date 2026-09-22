"""Tests for admin package add/edit routes."""
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from models.package import TourPackage


FAKE_UPLOAD = {
    "path": "https://res.cloudinary.com/test/image/upload/v1/test.jpg",
    "size_kb": 120.5,
    "uploaded_at": datetime.now(timezone.utc),
}


def _valid_package_form(**overrides):
    data = dict(
        title="Palawan Adventure",
        description="Explore beautiful Palawan islands.",
        destination="Palawan",
        duration_days="5",
        price="9999",
        currency="PHP",
    )
    data.update(overrides)
    return data


def _make_package(db, **overrides):
    defaults = dict(
        title="Existing Package",
        description="An existing package.",
        destination="Cebu",
        duration_days=3,
        price=5000.00,
        currency="PHP",
        is_active=True,
    )
    defaults.update(overrides)
    pkg = TourPackage(**defaults)
    db.session.add(pkg)
    db.session.commit()
    return pkg


class TestAddPackage:
    def test_requires_login(self, client):
        response = client.post("/admin/packages/add", data=_valid_package_form())
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        authenticated_client.post("/admin/packages/add", data=_valid_package_form())
        assert TourPackage.query.count() == 0

    def test_get_renders_form(self, app, admin_client):
        response = admin_client.get("/admin/packages/add")
        assert response.status_code == 200

    def test_valid_post_creates_package(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form())
        assert TourPackage.query.filter_by(title="Palawan Adventure").count() == 1

    def test_missing_title_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form(title=""))
        assert TourPackage.query.count() == 0

    def test_missing_description_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form(description=""))
        assert TourPackage.query.count() == 0

    def test_missing_destination_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form(destination=""))
        assert TourPackage.query.count() == 0

    def test_zero_duration_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form(duration_days="0"))
        assert TourPackage.query.count() == 0

    def test_negative_price_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form(price="-100"))
        assert TourPackage.query.count() == 0

    def test_default_image_used_when_no_file(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form())
        pkg = TourPackage.query.first()
        assert pkg is not None
        assert pkg.image == "default_tour.jpg"

    def test_image_upload_sets_cloudinary_url(self, app, admin_client):
        from app import db
        from io import BytesIO

        with patch("image_service.ImageUploadService.upload_and_compress", return_value=FAKE_UPLOAD):
            data = _valid_package_form()
            data["image"] = (BytesIO(b"fake image data"), "tour.jpg")
            admin_client.post(
                "/admin/packages/add",
                data=data,
                content_type="multipart/form-data",
            )
        pkg = TourPackage.query.first()
        assert pkg is not None
        assert pkg.image == FAKE_UPLOAD["path"]

    def test_redirects_to_packages_list_on_success(self, app, admin_client):
        response = admin_client.post(
            "/admin/packages/add",
            data=_valid_package_form(),
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin/packages" in response.headers["Location"]

    def test_package_type_is_derived_from_country_not_the_form(self, app, admin_client):
        """package_type is no longer an admin field - it's worked out
        from the selected country, so a value posted directly is
        ignored rather than trusted."""
        from app import db
        from models.continent import Continent
        from models.country import Country

        continent = Continent(name="Asia", is_active=True)
        db.session.add(continent)
        db.session.commit()
        ph = Country(name="Philippines", continent_id=continent.id, is_active=True)
        db.session.add(ph)
        db.session.commit()

        admin_client.post(
            "/admin/packages/add",
            data=_valid_package_form(country_id=str(ph.id), package_type="international"),
        )
        pkg = TourPackage.query.first()
        assert pkg.package_type == "domestic"

    def test_package_type_is_international_for_a_non_ph_country(self, app, admin_client):
        from app import db
        from models.continent import Continent
        from models.country import Country

        continent = Continent(name="Asia", is_active=True)
        db.session.add(continent)
        db.session.commit()
        jp = Country(name="Japan", continent_id=continent.id, is_active=True)
        db.session.add(jp)
        db.session.commit()

        admin_client.post("/admin/packages/add", data=_valid_package_form(country_id=str(jp.id)))
        pkg = TourPackage.query.first()
        assert pkg.package_type == "international"

    def test_package_type_falls_back_to_international_with_no_country(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form())
        pkg = TourPackage.query.first()
        assert pkg.package_type == "international"


class TestEditPackage:
    def test_requires_login(self, app, client):
        from app import db

        pkg = _make_package(db)
        response = client.post(f"/admin/packages/edit/{pkg.id}", data=_valid_package_form())
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        pkg = _make_package(db)
        authenticated_client.post(
            f"/admin/packages/edit/{pkg.id}",
            data=_valid_package_form(title="Hacked Title"),
        )
        assert db.session.get(TourPackage, pkg.id).title == "Existing Package"

    def test_get_renders_form(self, app, admin_client):
        from app import db

        pkg = _make_package(db)
        response = admin_client.get(f"/admin/packages/edit/{pkg.id}")
        assert response.status_code == 200

    def test_valid_post_updates_package(self, app, admin_client):
        from app import db

        pkg = _make_package(db)
        admin_client.post(
            f"/admin/packages/edit/{pkg.id}",
            data=_valid_package_form(title="Updated Title", description="Updated desc.", destination="Boracay"),
        )
        updated = db.session.get(TourPackage, pkg.id)
        assert updated.title == "Updated Title"
        assert updated.destination == "Boracay"

    def test_missing_title_does_not_update(self, app, admin_client):
        from app import db

        pkg = _make_package(db)
        admin_client.post(
            f"/admin/packages/edit/{pkg.id}",
            data=_valid_package_form(title=""),
        )
        assert db.session.get(TourPackage, pkg.id).title == "Existing Package"

    def test_image_upload_updates_package_image(self, app, admin_client):
        from app import db
        from io import BytesIO

        pkg = _make_package(db)
        with patch("image_service.ImageUploadService.upload_and_compress", return_value=FAKE_UPLOAD):
            with patch("utils.delete_old_image"):
                data = _valid_package_form(title="Existing Package", description="An existing package.", destination="Cebu")
                data["image"] = (BytesIO(b"fake image data"), "new.jpg")
                admin_client.post(
                    f"/admin/packages/edit/{pkg.id}",
                    data=data,
                    content_type="multipart/form-data",
                )
        assert db.session.get(TourPackage, pkg.id).image == FAKE_UPLOAD["path"]

    def test_nonexistent_package_redirects(self, app, admin_client):
        response = admin_client.get("/admin/packages/edit/99999", follow_redirects=False)
        assert response.status_code in (302, 404)


class TestPackageDisplayNumber:
    """The admin list shows a position number, not the database ID - IDs
    are never reused after deletes, so they drift above the real count."""

    def test_numbers_match_the_count_not_the_id_after_deletes(self, app, admin_client):
        from app import db

        pkgs = [_make_package(db, title=f"Package {i}") for i in range(5)]
        # Delete three, leaving gaps in the ID sequence
        for pkg in pkgs[:3]:
            db.session.delete(pkg)
        db.session.commit()
        surviving = pkgs[3:]
        assert max(p.id for p in surviving) == 5  # ID still 5 despite only 2 left

        page = admin_client.get("/admin/packages").get_data(as_text=True)
        assert "#2 · " in page
        assert "#1 · " in page
        assert "#5 · " not in page

    def test_numbers_continue_correctly_onto_the_second_page(self, app, admin_client):
        from app import db

        for i in range(25):  # 20 per page, so 5 spill onto page 2
            _make_package(db, title=f"Package {i}")

        page1 = admin_client.get("/admin/packages").get_data(as_text=True)
        page2 = admin_client.get("/admin/packages?page=2").get_data(as_text=True)
        assert "#25 · " in page1 and "#6 · " in page1
        assert "#5 · " in page2 and "#1 · " in page2
        assert "#6 · " not in page2


class TestDeletePackageCleansUpItineraryPhotos:
    def test_itinerary_day_photos_are_deleted_from_storage(self, app, admin_client, monkeypatch):
        from app import db
        from models.itinerary_day import ItineraryDay
        import routes.admin as admin_routes

        pkg = _make_package(db)
        db.session.add(ItineraryDay(package_id=pkg.id, day_number=1, title="Day 1", order=1,
                                    image="https://res.cloudinary.com/demo/image/upload/day1.jpg"))
        db.session.add(ItineraryDay(package_id=pkg.id, day_number=2, title="Day 2", order=2,
                                    image="https://res.cloudinary.com/demo/image/upload/day2.jpg"))
        db.session.commit()

        deleted = []
        monkeypatch.setattr(admin_routes, "delete_old_image", lambda path, *a, **k: deleted.append(path))

        admin_client.post(f"/admin/packages/delete/{pkg.id}")

        assert "https://res.cloudinary.com/demo/image/upload/day1.jpg" in deleted
        assert "https://res.cloudinary.com/demo/image/upload/day2.jpg" in deleted
        assert db.session.get(TourPackage, pkg.id) is None


class TestPriceOnRequest:
    """Packages without a fixed price can be marked "Price on request"."""

    def test_add_package_on_request_needs_no_price(self, app, admin_client):
        admin_client.post("/admin/packages/add",
                          data={**_valid_package_form(price=""), "price_on_request": "on"})
        pkg = TourPackage.query.one()
        assert pkg.price_on_request is True
        assert pkg.price is None
        assert pkg.has_price is False and pkg.formatted_price is None

    def test_fixed_price_package_still_requires_a_price(self, app, admin_client):
        response = admin_client.post("/admin/packages/add", data=_valid_package_form(price=""),
                                     follow_redirects=True)
        assert TourPackage.query.count() == 0
        assert b"Price on request" in response.data

    def test_edit_can_switch_to_on_request_and_back(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        admin_client.post(f"/admin/packages/edit/{pkg.id}",
                          data={**_valid_package_form(price=""), "price_on_request": "on"})
        db.session.refresh(pkg)
        assert pkg.price_on_request is True and pkg.price is None

        admin_client.post(f"/admin/packages/edit/{pkg.id}", data=_valid_package_form(price="7999"))
        db.session.refresh(pkg)
        assert pkg.price_on_request is False and float(pkg.price) == 7999

    def test_formatted_price_uses_the_right_symbol(self, app):
        assert TourPackage(price=5499, currency="PHP").formatted_price == "₱5,499"
        assert TourPackage(price=1200, currency="USD").formatted_price == "$1,200"
        assert TourPackage(price=900, currency="EUR").formatted_price == "€900"


class TestPriceOnRequestPublicPages:
    def _on_request_package(self, db):
        pkg = _make_package(db, title="Europe Custom Tour", price=None, price_on_request=True)
        return pkg

    def test_package_page_shows_price_on_request_and_no_breakdown(self, app, client):
        from app import db
        pkg = self._on_request_package(db)
        page = client.get(f"/packages/{pkg.id}").get_data(as_text=True)
        assert "Price on request" in page
        assert "price-breakdown" not in page.split("<script")[0].split("booking-sidebar")[-1]
        assert "₱None" not in page and "None /" not in page

    def test_search_data_leaves_price_out(self, app, client):
        import json, re
        from app import db
        pkg = self._on_request_package(db)
        page = client.get(f"/packages/{pkg.id}").get_data(as_text=True)
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1)
        data = json.loads(block)  # must still be valid JSON
        assert "price" not in data["offers"]

    def test_listing_card_shows_price_on_request(self, app, client):
        from app import db
        self._on_request_package(db)
        page = client.get("/packages/").get_data(as_text=True)
        assert "Price on request" in page

    def test_admin_list_shows_on_request(self, app, admin_client):
        from app import db
        self._on_request_package(db)
        assert "On request" in admin_client.get("/admin/packages").get_data(as_text=True)

    def test_fixed_price_package_unchanged(self, app, client):
        from app import db
        pkg = _make_package(db, price=5499)
        page = client.get(f"/packages/{pkg.id}").get_data(as_text=True)
        assert "₱5,499" in page
        assert "price-breakdown" in page
