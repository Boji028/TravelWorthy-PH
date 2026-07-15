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

    def test_forgot_password_does_not_crash_with_no_email_and_no_remote_addr(self, client):
        """Regression test: the rate-limit key_func used to do
        request.form.get("email", request.remote_addr).lower() with no
        None guard. A request with no 'email' form field AND no
        remote_addr (both fall through to the lambda's default) used to
        crash with an uncaught AttributeError — a 500 — before the view
        even ran, rather than reaching the route's own validation."""
        response = client.post(
            "/auth/forgot-password",
            data={},
            environ_overrides={"REMOTE_ADDR": None},
        )
        assert response.status_code != 500

    def test_forgot_password_page_views_are_not_rate_limited(self, client):
        """Regression test — the 5/hour limit used to apply to the whole
        route, so five GET page views from one IP consumed the quota and
        the sixth visitor got a 429 without ever submitting anything.
        The limit is meant to throttle email-sending POSTs only."""
        for _ in range(7):
            response = client.get("/auth/forgot-password")
            assert response.status_code == 200

    def test_proxyfix_builds_https_reset_link_behind_forwarded_proto_header(self, app, test_user, client, monkeypatch):
        """Regression test for ProxyFix. Render (and any PaaS) terminates
        HTTPS at a reverse proxy in front of the container — the app
        itself only ever sees plain HTTP internally unless something
        reads the X-Forwarded-Proto header the proxy sets. Without
        ProxyFix, url_for(_external=True) — used here for the reset link,
        and the same way for the Google OAuth redirect_uri — would build
        an http:// URL even for a visitor on https://, which is exactly
        what causes Google's redirect_uri_mismatch error even when the
        console's configured URI is correct."""
        from app import mail as app_mail

        app.config["MAIL_USERNAME"] = "test@example.com"
        sent_messages = []
        monkeypatch.setattr(app_mail, "send", lambda msg: sent_messages.append(msg))

        client.post(
            "/auth/forgot-password",
            data={"email": test_user.email},
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "travelworthyph.com"},
        )

        assert len(sent_messages) == 1
        assert "https://travelworthyph.com/auth/reset-password/" in sent_messages[0].body

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

    def test_password_reset_invalidates_other_active_sessions(self, app, test_user):
        """The core session-invalidation fix: a session already logged in
        before a password reset must stop working once the reset
        completes. Without this, resetting your password because you
        suspect your account is compromised leaves an already-open
        session (the attacker's) logged in right through the reset —
        defeating the entire point of doing it.

        Flask-Login caches the loaded user into flask.g, which is scoped
        to the *app context* rather than the request — the `app` fixture
        deliberately keeps one app context open for the whole test (see
        its docstring, to avoid a DetachedInstanceError elsewhere), so
        without clearing g between each simulated "device" here, the
        first device's cached user would leak into checks against the
        second device's genuinely separate session cookie. This isn't a
        real bug: in an actual deployment, every incoming request gets
        its own fresh context naturally.
        """
        from flask import g
        from app import db

        # "Device A": log in for real through the actual route so this
        # session cookie carries the token-based get_id() format — the
        # authenticated_client fixture bypasses get_id() entirely by
        # setting the session key directly, which wouldn't exercise this
        # code path at all.
        device_a = app.test_client()
        device_a.post("/auth/login", data={"email": test_user.email, "password": "TestPass123!"})
        g.pop("_login_user", None)
        assert device_a.get("/my-inquiries").status_code == 200  # confirms actually logged in
        g.pop("_login_user", None)

        # Reset the password from an entirely separate session/device.
        token_obj = PasswordResetToken.generate_token(test_user.id)
        db.session.add(token_obj)
        db.session.commit()
        device_b = app.test_client()
        device_b.post(
            f"/auth/reset-password/{token_obj.token}",
            data={"password": "BrandNewPass123", "confirm_password": "BrandNewPass123"},
        )
        g.pop("_login_user", None)

        # Device A's original session must now be dead — redirected to
        # login (Flask-Login's default for an unauthenticated request to
        # a @login_required route), not still authenticated.
        response = device_a.get("/my-inquiries")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    def test_password_reset_does_not_invalidate_the_new_login_itself(self, app, test_user):
        """Sanity check the fix isn't overly broad: logging in *after* the
        reset, with the new password, must work normally — only sessions
        that predate the reset should be affected."""
        token_obj = PasswordResetToken.generate_token(test_user.id)
        from app import db

        db.session.add(token_obj)
        db.session.commit()

        client = app.test_client()
        client.post(
            f"/auth/reset-password/{token_obj.token}",
            data={"password": "BrandNewPass123", "confirm_password": "BrandNewPass123"},
        )
        client.post("/auth/login", data={"email": test_user.email, "password": "BrandNewPass123"})

        assert client.get("/my-inquiries").status_code == 200

    def test_login_page_links_to_forgot_password(self, client):
        """Test the login page's Forgot password link points at the real route, not a placeholder."""
        response = client.get("/auth/login")
        assert b'href="/auth/forgot-password"' in response.data
