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

    def test_package_type_defaults_to_domestic(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form())
        pkg = TourPackage.query.first()
        assert pkg.package_type == "domestic"

    def test_package_type_international_saved(self, app, admin_client):
        from app import db

        admin_client.post("/admin/packages/add", data=_valid_package_form(package_type="international"))
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
