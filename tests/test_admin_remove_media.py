"""Tests for admin media removal endpoints."""
from unittest.mock import patch
from models.package import TourPackage
from models.blog import BlogPost
from models.package_image import PackageImage
from models.continent import Continent
from models.country import Country


def _make_package(db, **overrides):
    defaults = dict(
        title="Tour Package",
        description="A tour.",
        destination="Palawan",
        duration_days=5,
        price=5000.00,
        currency="PHP",
        image="default_tour.jpg",
        is_active=True,
    )
    defaults.update(overrides)
    pkg = TourPackage(**defaults)
    db.session.add(pkg)
    db.session.commit()
    return pkg


def _make_post(db, **overrides):
    defaults = dict(title="A Post", content="<p>Content.</p>", is_published=True)
    defaults.update(overrides)
    post = BlogPost(**defaults)
    db.session.add(post)
    db.session.commit()
    return post


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


class TestRemovePackagePhoto:
    def test_requires_login(self, client):
        response = client.post("/admin/packages/remove-photo/1")
        assert response.status_code in (302, 401, 403)

    def test_sets_image_to_none(self, app, admin_client):
        from app import db

        pkg = _make_package(db, image="https://cdn.example.com/photo.jpg")
        with patch("utils.delete_old_image"):
            admin_client.post(f"/admin/packages/remove-photo/{pkg.id}")
        updated = db.session.get(TourPackage, pkg.id)
        assert updated.image is None or updated.image == "default_tour.jpg"

    def test_default_image_not_deleted(self, app, admin_client):
        from app import db

        pkg = _make_package(db, image="default_tour.jpg")
        with patch("utils.delete_old_image") as mock_delete:
            admin_client.post(f"/admin/packages/remove-photo/{pkg.id}")
        mock_delete.assert_not_called()

    def test_nonexistent_package_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/packages/remove-photo/99999")
        assert response.status_code == 404

    def test_redirects_to_edit_page(self, app, admin_client):
        from app import db

        pkg = _make_package(db)
        response = admin_client.post(
            f"/admin/packages/remove-photo/{pkg.id}",
            follow_redirects=False,
        )
        assert response.status_code == 302


class TestRemoveFlier:
    def test_requires_login(self, client):
        response = client.post("/admin/fliers/1/remove")
        assert response.status_code in (302, 401, 403)

    def test_clears_flier_image(self, app, admin_client):
        from app import db

        pkg = _make_package(db, flier_image="https://cdn.example.com/flier.jpg")
        with patch("image_service.ImageUploadService.delete_image"):
            admin_client.post(f"/admin/fliers/{pkg.id}/remove")
        updated = db.session.get(TourPackage, pkg.id)
        assert updated.flier_image is None

    def test_nonexistent_package_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/fliers/99999/remove")
        assert response.status_code == 404

    def test_redirects_on_success(self, app, admin_client):
        from app import db

        pkg = _make_package(db, flier_image="https://cdn.example.com/flier.jpg")
        with patch("image_service.ImageUploadService.delete_image"):
            response = admin_client.post(
                f"/admin/fliers/{pkg.id}/remove",
                follow_redirects=False,
            )
        assert response.status_code == 302


class TestRemoveBlogPhoto:
    def test_requires_login(self, client):
        response = client.post("/admin/blog/remove-photo/1")
        assert response.status_code in (302, 401, 403)

    def test_clears_featured_image(self, app, admin_client):
        from app import db

        post = _make_post(db, featured_image="https://cdn.example.com/blog.jpg")
        with patch("utils.delete_old_image"):
            admin_client.post(f"/admin/blog/remove-photo/{post.id}")
        updated = db.session.get(BlogPost, post.id)
        assert updated.featured_image is None

    def test_nonexistent_post_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/blog/remove-photo/99999")
        assert response.status_code == 404

    def test_redirects_on_success(self, app, admin_client):
        from app import db

        post = _make_post(db)
        response = admin_client.post(
            f"/admin/blog/remove-photo/{post.id}",
            follow_redirects=False,
        )
        assert response.status_code == 302


class TestDeleteGalleryImage:
    def test_requires_login(self, client):
        response = client.post("/admin/packages/delete-gallery-image/1")
        assert response.status_code in (302, 401, 403)

    def test_deletes_gallery_image(self, app, admin_client):
        from app import db

        pkg = _make_package(db)
        img = PackageImage(
            package_id=pkg.id,
            path="https://cdn.example.com/gallery.jpg",
        )
        db.session.add(img)
        db.session.commit()
        img_id = img.id
        with patch("utils.delete_old_image"):
            admin_client.post(f"/admin/packages/delete-gallery-image/{img_id}")
        assert db.session.get(PackageImage, img_id) is None

    def test_nonexistent_image_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/packages/delete-gallery-image/99999")
        assert response.status_code == 404

    def test_redirects_to_edit_page(self, app, admin_client):
        from app import db

        pkg = _make_package(db)
        img = PackageImage(
            package_id=pkg.id,
            path="https://cdn.example.com/gallery2.jpg",
        )
        db.session.add(img)
        db.session.commit()
        with patch("utils.delete_old_image"):
            response = admin_client.post(
                f"/admin/packages/delete-gallery-image/{img.id}",
                follow_redirects=False,
            )
        assert response.status_code == 302


class TestRemoveContinentImage:
    def test_requires_login(self, client):
        response = client.post("/admin/continents/remove-image/1")
        assert response.status_code in (302, 401, 403)

    def test_clears_continent_image(self, app, admin_client):
        from app import db

        continent = _make_continent(db, image="https://cdn.example.com/asia.jpg")
        with patch("utils.delete_old_image"):
            admin_client.post(f"/admin/continents/remove-image/{continent.id}")
        updated = db.session.get(Continent, continent.id)
        assert updated.image is None

    def test_nonexistent_continent_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/continents/remove-image/99999")
        assert response.status_code == 404

    def test_redirects_on_success(self, app, admin_client):
        from app import db

        continent = _make_continent(db, image="https://cdn.example.com/asia.jpg")
        with patch("utils.delete_old_image"):
            response = admin_client.post(
                f"/admin/continents/remove-image/{continent.id}",
                follow_redirects=False,
            )
        assert response.status_code == 302


class TestRemoveCountryImage:
    def test_requires_login(self, client):
        response = client.post("/admin/countries/remove-image/1")
        assert response.status_code in (302, 401, 403)

    def test_clears_country_image(self, app, admin_client):
        from app import db

        country = _make_country(db, image="https://cdn.example.com/ph.jpg")
        with patch("utils.delete_old_image"):
            admin_client.post(f"/admin/countries/remove-image/{country.id}")
        updated = db.session.get(Country, country.id)
        assert updated.image is None

    def test_nonexistent_country_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/countries/remove-image/99999")
        assert response.status_code == 404

    def test_redirects_on_success(self, app, admin_client):
        from app import db

        country = _make_country(db, image="https://cdn.example.com/ph.jpg")
        with patch("utils.delete_old_image"):
            response = admin_client.post(
                f"/admin/countries/remove-image/{country.id}",
                follow_redirects=False,
            )
        assert response.status_code == 302


class TestCloudinarySignature:
    def test_requires_login(self, client):
        response = client.post("/admin/cloudinary-signature", json={})
        assert response.status_code in (302, 401, 403)

    def test_returns_json(self, app, admin_client):
        response = admin_client.post("/admin/cloudinary-signature", json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None

    def test_response_has_signature_fields(self, app, admin_client):
        response = admin_client.post("/admin/cloudinary-signature", json={})
        data = response.get_json()
        assert "signature" in data or "timestamp" in data
