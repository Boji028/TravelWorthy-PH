"""Tests for the forgot-password / reset-password functionality."""
import pytest
from datetime import datetime, timezone, timedelta
from werkzeug.security import check_password_hash
from models.user import User
from models.password_reset import PasswordResetToken
from password_reset_service import PasswordResetService


class TestPasswordResetToken:
    """Test PasswordResetToken model."""

    def test_generate_token(self, test_user):
        """Test token generation."""
        token = PasswordResetToken.generate_token(test_user.id)

        assert token.user_id == test_user.id
        assert token.token is not None
        assert len(token.token) > 0
        assert token.is_used is False
        assert token.used_at is None

    def test_token_expiration(self, test_user, app):
        """Test token expiration check."""
        token_obj = PasswordResetToken.generate_token(test_user.id, expires_in_hours=1)

        assert token_obj.is_valid() is True

        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        assert token_obj.is_valid() is False

    def test_get_valid_token(self, test_user, app):
        """Test retrieving a valid token."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        retrieved = PasswordResetToken.get_valid_token(token_obj.token)
        assert retrieved is not None
        assert retrieved.user_id == test_user.id

    def test_get_invalid_token(self, app):
        """Test retrieving an invalid token."""
        retrieved = PasswordResetToken.get_valid_token("invalid_token")
        assert retrieved is None

    def test_consume_token(self, test_user, app):
        """Test consuming a token marks it used."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        result = token_obj.consume()
        assert result is True
        assert token_obj.is_used is True
        assert token_obj.used_at is not None

    def test_consume_already_used_token(self, test_user, app):
        """Test consuming an already-used token fails."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        token_obj.consume()
        db.session.commit()

        result = token_obj.consume()
        assert result is False


class TestPasswordResetService:
    """Test PasswordResetService."""

    def test_request_reset_existing_user(self, test_user, app, monkeypatch):
        """Test requesting a reset for an existing user with a password creates a token and sends mail."""
        monkeypatch.setattr(PasswordResetService, "_send_reset_email", staticmethod(lambda *args, **kwargs: True))

        success, message = PasswordResetService.request_reset(test_user.email)

        assert success is True
        assert "If an account" in message
        tokens = PasswordResetToken.query.filter_by(user_id=test_user.id, is_used=False).all()
        assert len(tokens) == 1

    def test_request_reset_nonexistent_user(self, app):
        """Test requesting a reset for a non-existent email returns the same generic message (no account-existence leak)."""
        success, message = PasswordResetService.request_reset("nobody@example.com")

        assert success is True
        assert "If an account" in message

    def test_request_reset_oauth_only_account(self, app):
        """Test requesting a reset for a Google-only account (no password) is a no-op, same generic message."""
        from app import db

        oauth_user = User(name="Google User", email="googleuser@example.com", password=None, oauth_provider="google", oauth_id="12345")
        db.session.add(oauth_user)
        db.session.commit()

        success, message = PasswordResetService.request_reset("googleuser@example.com")

        assert success is True
        assert "If an account" in message
        tokens = PasswordResetToken.query.filter_by(user_id=oauth_user.id).all()
        assert len(tokens) == 0

    def test_request_reset_invalidates_previous_tokens(self, test_user, app, monkeypatch):
        """Requesting a new reset should invalidate any previous unused token for that user."""
        monkeypatch.setattr(PasswordResetService, "_send_reset_email", staticmethod(lambda *args, **kwargs: True))

        PasswordResetService.request_reset(test_user.email)
        first_token = PasswordResetToken.query.filter_by(user_id=test_user.id, is_used=False).first()

        PasswordResetService.request_reset(test_user.email)

        from app import db

        db.session.refresh(first_token)
        assert first_token.is_used is True

    def test_reset_password_success(self, test_user, app):
        """Test completing a reset with a valid token updates the password hash."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        success, message, user = PasswordResetService.reset_password(token_obj.token, "NewSecurePass123")

        assert success is True
        assert user is not None
        assert check_password_hash(user.password, "NewSecurePass123")

        db.session.refresh(token_obj)
        assert token_obj.is_used is True

    def test_reset_password_invalid_token(self, app):
        """Test resetting with an invalid token fails cleanly."""
        success, message, user = PasswordResetService.reset_password("invalid_token", "NewSecurePass123")

        assert success is False
        assert user is None

    def test_reset_password_expired_token(self, test_user, app):
        """Test resetting with an expired token fails."""
        token_obj = PasswordResetToken.generate_token(test_user.id, expires_in_hours=-1)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        success, message, user = PasswordResetService.reset_password(token_obj.token, "NewSecurePass123")

        assert success is False
        assert user is None


class TestPasswordResetRoutes:
    """Test forgot-password / reset-password routes."""

    def test_forgot_password_get_renders_form(self, client):
        """Test the forgot password page renders."""
        response = client.get("/auth/forgot-password")
        assert response.status_code == 200

    def test_forgot_password_post_existing_user(self, client, test_user, monkeypatch):
        """Test submitting the forgot password form for a real user."""
        monkeypatch.setattr(PasswordResetService, "_send_reset_email", staticmethod(lambda *args, **kwargs: True))

        response = client.post("/auth/forgot-password", data={"email": test_user.email}, follow_redirects=True)

        assert response.status_code == 200
        tokens = PasswordResetToken.query.filter_by(user_id=test_user.id, is_used=False).all()
        assert len(tokens) == 1

    def test_forgot_password_post_nonexistent_user(self, client):
        """Test submitting the forgot password form for a non-existent email still returns 200 with generic message."""
        response = client.post("/auth/forgot-password", data={"email": "nobody@example.com"}, follow_redirects=True)

        assert response.status_code == 200
        assert b"If an account" in response.data

    def test_reset_password_get_with_valid_token_renders_form(self, client, test_user, app):
        """Test the reset password page renders for a valid token."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        response = client.get(f"/auth/reset-password/{token_obj.token}")
        assert response.status_code == 200

    def test_reset_password_get_with_invalid_token_redirects(self, client):
        """Test the reset password page redirects for an invalid token."""
        response = client.get("/auth/reset-password/invalid_token", follow_redirects=True)

        assert response.status_code == 200
        assert b"forgot" in response.request.path.encode() or b"invalid" in response.data.lower()

    def test_reset_password_post_valid_token_updates_password(self, client, test_user, app):
        """Test submitting a new password with a valid token actually changes it."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        response = client.post(
            f"/auth/reset-password/{token_obj.token}",
            data={"password": "BrandNewPass123", "confirm_password": "BrandNewPass123"},
            follow_redirects=True,
        )

        assert response.status_code == 200

        user = db.session.get(User, test_user.id)
        assert check_password_hash(user.password, "BrandNewPass123")

    def test_reset_password_post_mismatched_confirmation_does_not_change_password(self, client, test_user, app):
        """Test mismatched password confirmation does not update the password."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        client.post(
            f"/auth/reset-password/{token_obj.token}",
            data={"password": "BrandNewPass123", "confirm_password": "DifferentPass123"},
            follow_redirects=True,
        )

        user = db.session.get(User, test_user.id)
        assert check_password_hash(user.password, "TestPass123!")

    def test_login_page_links_to_forgot_password(self, client):
        """Test the login page's Forgot password link points at the real route, not a placeholder."""
        response = client.get("/auth/login")
        assert b'href="/auth/forgot-password"' in response.data
