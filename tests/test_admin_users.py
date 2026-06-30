"""Tests for admin user management routes (toggle admin, delete user)."""
from models.user import User
from models.testimonial import Testimonial
from werkzeug.security import generate_password_hash


def _make_user(db, **overrides):
    defaults = dict(
        name='Regular User',
        email='user@example.com',
        password=generate_password_hash('TestPass123'),
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
        response = client.post('/admin/users/toggle-admin/1')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        user = _make_user(db)
        authenticated_client.post(f'/admin/users/toggle-admin/{user.id}')
        assert db.session.get(User, user.id).is_admin is False

    def test_promotes_regular_user_to_admin(self, app, admin_client):
        from app import db
        user = _make_user(db)
        admin_client.post(f'/admin/users/toggle-admin/{user.id}')
        assert db.session.get(User, user.id).is_admin is True

    def test_demotes_admin_to_regular(self, app, admin_client):
        from app import db
        user = _make_user(db, is_admin=True, email='other@example.com')
        admin_client.post(f'/admin/users/toggle-admin/{user.id}')
        assert db.session.get(User, user.id).is_admin is False

    def test_cannot_change_own_admin_status(self, app, admin_client, admin_user):
        from app import db
        admin_client.post(f'/admin/users/toggle-admin/{admin_user.id}')
        assert db.session.get(User, admin_user.id).is_admin is True

    def test_cannot_remove_last_admin(self, app, admin_client, admin_user):
        from app import db
        admin_client.post(f'/admin/users/toggle-admin/{admin_user.id}')
        assert db.session.get(User, admin_user.id).is_admin is True

    def test_nonexistent_user_returns_404(self, app, admin_client):
        response = admin_client.post('/admin/users/toggle-admin/99999')
        assert response.status_code == 404


class TestDeleteUser:
    def test_requires_login(self, client):
        response = client.post('/admin/users/delete/1')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client, test_user):
        from app import db
        user = _make_user(db, email='victim@example.com')
        authenticated_client.post(f'/admin/users/delete/{user.id}')
        assert db.session.get(User, user.id) is not None

    def test_admin_can_delete_regular_user(self, app, admin_client):
        from app import db
        user = _make_user(db)
        user_id = user.id
        admin_client.post(f'/admin/users/delete/{user_id}')
        assert db.session.get(User, user_id) is None

    def test_cannot_delete_own_account(self, app, admin_client, admin_user):
        from app import db
        admin_client.post(f'/admin/users/delete/{admin_user.id}')
        assert db.session.get(User, admin_user.id) is not None

    def test_cannot_delete_last_admin(self, app, admin_client, admin_user):
        from app import db
        admin_client.post(f'/admin/users/delete/{admin_user.id}')
        assert db.session.get(User, admin_user.id) is not None

    def test_blocked_when_user_has_testimonial(self, app, admin_client):
        from app import db
        user = _make_user(db)
        testimonial = Testimonial(user_id=user.id, message='Great trip!', rating=5)
        db.session.add(testimonial)
        db.session.commit()
        user_id = user.id
        admin_client.post(f'/admin/users/delete/{user_id}')
        assert db.session.get(User, user_id) is not None

    def test_nonexistent_user_returns_404(self, app, admin_client):
        response = admin_client.post('/admin/users/delete/99999')
        assert response.status_code == 404

    def test_delete_redirects_to_users_list(self, app, admin_client):
        from app import db
        user = _make_user(db)
        response = admin_client.post(
            f'/admin/users/delete/{user.id}', follow_redirects=False
        )
        assert response.status_code == 302
        assert '/admin/users' in response.headers['Location']
