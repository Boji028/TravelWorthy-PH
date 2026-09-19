"""Tests for admin user management routes (toggle admin, delete user)."""
from models.user import User
from models.testimonial import Testimonial
from werkzeug.security import generate_password_hash


def _make_user(db, **overrides):
    defaults = dict(
        name="Regular User",
        email="user@example.com",
        password=generate_password_hash("TestPass123"),
        is_admin=False,
        email_verified=True,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db.session.add(user)
    db.session.commit()
    return user


class TestToggleUserAdmin:
    def test_requires_login(self, client):
        response = client.post("/admin/users/toggle-admin/1")
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        user = _make_user(db)
        authenticated_client.post(f"/admin/users/toggle-admin/{user.id}")
        assert db.session.get(User, user.id).is_admin is False

    def test_promotes_regular_user_to_admin(self, app, admin_client):
        from app import db

        user = _make_user(db)
        admin_client.post(f"/admin/users/toggle-admin/{user.id}")
        assert db.session.get(User, user.id).is_admin is True

    def test_demotes_admin_to_regular(self, app, admin_client):
        from app import db

        user = _make_user(db, is_admin=True, email="other@example.com")
        admin_client.post(f"/admin/users/toggle-admin/{user.id}")
        assert db.session.get(User, user.id).is_admin is False

    def test_cannot_change_own_admin_status(self, app, admin_client, admin_user):
        from app import db

        admin_client.post(f"/admin/users/toggle-admin/{admin_user.id}")
        assert db.session.get(User, admin_user.id).is_admin is True

    def test_cannot_remove_last_admin(self, app, admin_client, admin_user):
        from app import db

        admin_client.post(f"/admin/users/toggle-admin/{admin_user.id}")
        assert db.session.get(User, admin_user.id).is_admin is True

    def test_nonexistent_user_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/users/toggle-admin/99999")
        assert response.status_code == 404


class TestDeleteUser:
    def test_requires_login(self, client):
        response = client.post("/admin/users/delete/1")
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client, test_user):
        from app import db

        user = _make_user(db, email="victim@example.com")
        authenticated_client.post(f"/admin/users/delete/{user.id}")
        assert db.session.get(User, user.id) is not None

    def test_admin_can_delete_regular_user(self, app, admin_client):
        from app import db

        user = _make_user(db)
        user_id = user.id
        admin_client.post(f"/admin/users/delete/{user_id}")
        assert db.session.get(User, user_id) is None

    def test_cannot_delete_own_account(self, app, admin_client, admin_user):
        from app import db

        admin_client.post(f"/admin/users/delete/{admin_user.id}")
        assert db.session.get(User, admin_user.id) is not None

    def test_cannot_delete_last_admin(self, app, admin_client, admin_user):
        from app import db

        admin_client.post(f"/admin/users/delete/{admin_user.id}")
        assert db.session.get(User, admin_user.id) is not None

    def test_blocked_when_user_has_testimonial(self, app, admin_client):
        from app import db

        user = _make_user(db)
        testimonial = Testimonial(user_id=user.id, message="Great trip!", rating=5)
        db.session.add(testimonial)
        db.session.commit()
        user_id = user.id
        admin_client.post(f"/admin/users/delete/{user_id}")
        assert db.session.get(User, user_id) is not None

    def test_nonexistent_user_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/users/delete/99999")
        assert response.status_code == 404

    def test_delete_redirects_to_users_list(self, app, admin_client):
        from app import db

        user = _make_user(db)
        response = admin_client.post(f"/admin/users/delete/{user.id}", follow_redirects=False)
        assert response.status_code == 302
        assert "/admin/users" in response.headers["Location"]


class TestAddUser:
    """The public registration form is gone — this route is now the only
    way any new User row (always staff) gets created."""

    VALID_DATA = {
        "name": "New Staff",
        "email": "newstaff@example.com",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123",
    }

    def test_requires_login(self, client):
        response = client.post("/admin/users/add", data=self.VALID_DATA)
        assert response.status_code in (302, 401, 403)
        assert User.query.filter_by(email=self.VALID_DATA["email"]).first() is None

    def test_rejects_non_admin(self, authenticated_client):
        authenticated_client.post("/admin/users/add", data=self.VALID_DATA)
        assert User.query.filter_by(email=self.VALID_DATA["email"]).first() is None

    def test_admin_can_create_staff_account(self, admin_client):
        response = admin_client.post("/admin/users/add", data=self.VALID_DATA, follow_redirects=True)
        assert response.status_code == 200
        user = User.query.filter_by(email=self.VALID_DATA["email"]).first()
        assert user is not None
        assert user.name == "New Staff"

    def test_created_account_is_always_admin(self, admin_client):
        admin_client.post("/admin/users/add", data=self.VALID_DATA)
        user = User.query.filter_by(email=self.VALID_DATA["email"]).first()
        assert user.is_admin is True

    def test_created_account_can_log_in(self, app, admin_client):
        admin_client.post("/admin/users/add", data=self.VALID_DATA)
        # A fresh, unauthenticated client — admin_client's underlying
        # client is already logged in as the admin, so reusing it here
        # would short-circuit the login route before it does anything.
        # g.pop clears Flask-Login's current_user cache left over from
        # admin_client's own request, same fix used in
        # test_password_reset.py when switching test clients mid-test.
        from flask import g

        g.pop("_login_user", None)
        fresh_client = app.test_client()
        response = fresh_client.post(
            "/staff-portal",
            data={"email": self.VALID_DATA["email"], "password": self.VALID_DATA["password"]},
            follow_redirects=True,
        )
        assert b"Welcome back" in response.data

    def test_rejects_duplicate_email(self, admin_client, admin_user):
        response = admin_client.post(
            "/admin/users/add",
            data={**self.VALID_DATA, "email": admin_user.email},
            follow_redirects=True,
        )
        assert b"already exists" in response.data

    def test_rejects_mismatched_passwords(self, admin_client):
        admin_client.post("/admin/users/add", data={**self.VALID_DATA, "confirm_password": "DifferentPass123"})
        assert User.query.filter_by(email=self.VALID_DATA["email"]).first() is None

    def test_rejects_weak_password(self, admin_client):
        admin_client.post("/admin/users/add", data={**self.VALID_DATA, "password": "weak", "confirm_password": "weak"})
        assert User.query.filter_by(email=self.VALID_DATA["email"]).first() is None

    def test_rejects_missing_fields(self, admin_client):
        response = admin_client.post(
            "/admin/users/add",
            data={"name": "", "email": "", "password": "", "confirm_password": ""},
            follow_redirects=True,
        )
        assert b"required" in response.data
        assert User.query.filter_by(email="").first() is None
