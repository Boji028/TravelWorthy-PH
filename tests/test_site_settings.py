"""Tests for the Site Settings admin page.

Covers access control, the AJAX save flow (with mocked image uploads),
and the AJAX remove-image route.
"""
import io
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from models.site_settings import SiteSettings
from image_service import ImageUploadException


class TestSiteSettingsAccess:
    def test_settings_page_requires_login(self, client):
        response = client.get("/admin/site-settings")
        assert response.status_code in (302, 401, 403)

    def test_settings_page_rejects_non_admin_user(self, authenticated_client):
        response = authenticated_client.get("/admin/site-settings")
        assert response.status_code in (302, 403)

    def test_save_requires_login(self, client):
        response = client.post("/admin/site-settings", data={})
        assert response.status_code in (302, 401, 403)

    def test_remove_image_requires_login(self, client):
        response = client.post("/admin/site-settings/remove-image/hero_image")
        assert response.status_code in (302, 401, 403)


class TestSiteSettingsGet:
    def test_get_page_creates_settings_singleton_on_first_access(self, app, admin_client):
        assert SiteSettings.query.count() == 0
        response = admin_client.get("/admin/site-settings")
        assert response.status_code == 200
        assert SiteSettings.query.count() == 1

    def test_get_page_reuses_existing_singleton(self, app, admin_client):
        admin_client.get("/admin/site-settings")
        admin_client.get("/admin/site-settings")
        assert SiteSettings.query.count() == 1

    def test_last_saved_label_appears_after_creation(self, app, admin_client):
        response = admin_client.get("/admin/site-settings")
        page = response.get_data(as_text=True)
        assert "Last saved" in page


class TestSiteSettingsSave:
    def test_save_without_files_returns_success_json(self, app, admin_client):
        response = admin_client.post("/admin/site-settings", data={}, content_type="multipart/form-data")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Site settings updated!"
        assert data["images"]["hero_image"] is None
        assert data["images"]["testimonial_image"] is None
        assert data["images"]["cta_image"] is None

    def test_save_with_image_upload_updates_field(self, app, admin_client):
        fake_result = {
            "path": "https://res.cloudinary.com/test/hero.jpg",
            "size_kb": 245.7,
            "uploaded_at": datetime.now(timezone.utc),
        }
        with patch("image_service.ImageUploadService.upload_and_compress", return_value=fake_result):
            response = admin_client.post(
                "/admin/site-settings",
                data={"hero_image": (io.BytesIO(b"fake image bytes"), "hero.jpg")},
                content_type="multipart/form-data",
            )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["images"]["hero_image"]["url"] == "https://res.cloudinary.com/test/hero.jpg"

        settings = SiteSettings.get_settings()
        assert settings.hero_image == "https://res.cloudinary.com/test/hero.jpg"

    def test_save_with_failed_upload_returns_json_error(self, app, admin_client):
        with patch("image_service.ImageUploadService.upload_and_compress", side_effect=ImageUploadException("File too large")):
            response = admin_client.post(
                "/admin/site-settings",
                data={"hero_image": (io.BytesIO(b"fake image bytes"), "hero.jpg")},
                content_type="multipart/form-data",
            )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "upload failed" in data["message"].lower()


class TestSiteSettingsRemoveImage:
    def test_remove_image_clears_field_and_returns_json(self, app, admin_client):
        from app import db

        settings = SiteSettings.get_settings()
        settings.hero_image = "https://res.cloudinary.com/test/hero.jpg"
        settings.hero_image_size_kb = 245.7
        db.session.commit()

        response = admin_client.post("/admin/site-settings/remove-image/hero_image")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["field"] == "hero_image"

        db.session.refresh(settings)
        assert settings.hero_image is None
        assert settings.hero_image_size_kb is None

    def test_remove_image_invalid_field_returns_400(self, app, admin_client):
        response = admin_client.post("/admin/site-settings/remove-image/not_a_real_field")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_remove_image_when_none_set_returns_400(self, app, admin_client):
        SiteSettings.get_settings()
        response = admin_client.post("/admin/site-settings/remove-image/cta_image")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
