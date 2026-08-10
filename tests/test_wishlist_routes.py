"""Tests for wishlist toggle routes and the My Wishlist page."""
from models.visa import VisaCountry
from models.wishlist import WishlistItem


def _make_visa(db, **overrides):
    defaults = dict(country_name="Japan", is_active=True)
    defaults.update(overrides)
    visa = VisaCountry(**defaults)
    db.session.add(visa)
    db.session.commit()
    return visa


class TestTogglePackageWishlist:
    def test_requires_login(self, client, test_package):
        response = client.post(f"/wishlist/toggle/package/{test_package.id}")
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["login_required"] is True
        assert "login_url" in data

    def test_save_then_unsave(self, app, authenticated_client, test_user, test_package):
        response = authenticated_client.post(f"/wishlist/toggle/package/{test_package.id}")
        assert response.status_code == 200
        assert response.get_json() == {"success": True, "saved": True}
        assert WishlistItem.query.filter_by(user_id=test_user.id, package_id=test_package.id).count() == 1

        response = authenticated_client.post(f"/wishlist/toggle/package/{test_package.id}")
        assert response.get_json() == {"success": True, "saved": False}
        assert WishlistItem.query.filter_by(user_id=test_user.id, package_id=test_package.id).count() == 0

    def test_nonexistent_package_returns_404(self, authenticated_client):
        response = authenticated_client.post("/wishlist/toggle/package/99999")
        assert response.status_code == 404

    def test_does_not_affect_other_users_wishlist(self, app, authenticated_client, test_user, test_package):
        from app import db
        from models.user import User
        from werkzeug.security import generate_password_hash

        other = User(
            name="Other", email="other@example.com", password=generate_password_hash("Pass123"), email_verified=True
        )
        db.session.add(other)
        db.session.commit()
        other_item = WishlistItem(user_id=other.id, package_id=test_package.id)
        db.session.add(other_item)
        db.session.commit()

        authenticated_client.post(f"/wishlist/toggle/package/{test_package.id}")

        assert WishlistItem.query.filter_by(user_id=test_user.id, package_id=test_package.id).count() == 1
        assert db.session.get(WishlistItem, other_item.id) is not None


class TestToggleVisaWishlist:
    def test_requires_login(self, app, client):
        from app import db

        visa = _make_visa(db)
        response = client.post(f"/wishlist/toggle/visa/{visa.id}")
        assert response.status_code == 401
        assert response.get_json()["login_required"] is True

    def test_save_then_unsave(self, app, authenticated_client, test_user):
        from app import db

        visa = _make_visa(db)
        response = authenticated_client.post(f"/wishlist/toggle/visa/{visa.id}")
        assert response.status_code == 200
        assert response.get_json() == {"success": True, "saved": True}
        assert WishlistItem.query.filter_by(user_id=test_user.id, visa_id=visa.id).count() == 1

        response = authenticated_client.post(f"/wishlist/toggle/visa/{visa.id}")
        assert response.get_json() == {"success": True, "saved": False}
        assert WishlistItem.query.filter_by(user_id=test_user.id, visa_id=visa.id).count() == 0

    def test_nonexistent_visa_returns_404(self, authenticated_client):
        response = authenticated_client.post("/wishlist/toggle/visa/99999")
        assert response.status_code == 404

    def test_does_not_affect_other_users_wishlist(self, app, authenticated_client, test_user):
        from app import db
        from models.user import User
        from werkzeug.security import generate_password_hash

        visa = _make_visa(db)
        other = User(
            name="Other2", email="other2@example.com", password=generate_password_hash("Pass123"), email_verified=True
        )
        db.session.add(other)
        db.session.commit()
        other_item = WishlistItem(user_id=other.id, visa_id=visa.id)
        db.session.add(other_item)
        db.session.commit()

        authenticated_client.post(f"/wishlist/toggle/visa/{visa.id}")

        assert WishlistItem.query.filter_by(user_id=test_user.id, visa_id=visa.id).count() == 1
        assert db.session.get(WishlistItem, other_item.id) is not None


class TestMyWishlistPage:
    def test_requires_login(self, client):
        response = client.get("/wishlist/")
        assert response.status_code in (302, 401, 403)
