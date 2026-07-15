"""Tests for authentication routes."""
import pytest
from models.user import User
from werkzeug.security import check_password_hash


class TestUserRegistration:
    """Test user registration functionality."""

    def test_register_valid_user(self, client):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            data={
                "name": "New User",
                "email": "newuser@example.com",
                "phone": "+1234567890",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        user = User.query.filter_by(email="newuser@example.com").first()
        assert user is not None
        assert user.name == "New User"

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        response = client.post(
            "/auth/register",
            data={
                "name": "Another User",
                "email": test_user.email,
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
            },
            follow_redirects=True,
        )

        assert b"already registered" in response.data or b"already exists" in response.data

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/auth/register",
            data={"name": "New User", "email": "test@example.com", "password": "weak", "confirm_password": "weak"},
        )

        assert response.status_code == 200
        user = User.query.filter_by(email="test@example.com").first()
        assert user is None

    def test_register_passwords_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post(
            "/auth/register",
            data={
                "name": "New User",
                "email": "test@example.com",
                "password": "SecurePass123",
                "confirm_password": "DifferentPass123",
            },
        )

        assert response.status_code == 200
        user = User.query.filter_by(email="test@example.com").first()
        assert user is None

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/auth/register",
            data={
                "name": "New User",
                "email": "invalid-email",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
            },
        )

        assert response.status_code == 200
        user = User.query.filter_by(email="invalid-email").first()
        assert user is None

    def test_register_auto_verifies_when_verification_disabled(self, client, app):
        """Users should be immediately verified when the feature flag is off."""
        app.config["REQUIRE_EMAIL_VERIFICATION"] = False

        response = client.post(
            "/auth/register",
            data={
                "name": "Auto Verified",
                "email": "autoverified@example.com",
                "phone": "+1234567890",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        user = User.query.filter_by(email="autoverified@example.com").first()
        assert user is not None
        assert user.email_verified is True
        assert b"log in" in response.data.lower()


class TestUserLogin:
    """Test user login functionality."""

    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post(
            "/auth/login", data={"email": test_user.email, "password": "TestPass123!"}, follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Welcome back" in response.data

    def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login", data={"email": test_user.email, "password": "WrongPassword"}, follow_redirects=True
        )

        assert b"Invalid email or password" in response.data

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/auth/login", data={"email": "nonexistent@example.com", "password": "TestPass123!"}, follow_redirects=True
        )

        assert b"Invalid email or password" in response.data

    def test_login_case_insensitive_email(self, client, test_user):
        """Test login with different email case."""
        response = client.post(
            "/auth/login", data={"email": test_user.email.upper(), "password": "TestPass123!"}, follow_redirects=True
        )

        assert response.status_code == 200


class TestUserLogout:
    """Test user logout functionality."""

    def test_logout(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.get("/auth/logout", follow_redirects=True)

        assert response.status_code == 200
        assert b"logged out" in response.data


class TestPasswordChange:
    """Test password change functionality."""

    def test_change_password_success(self, authenticated_client, test_user):
        """Test successful password change."""
        response = authenticated_client.post(
            "/auth/profile",
            data={
                "current_password": "TestPass123!",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
            follow_redirects=True,
        )

        assert b"changed successfully" in response.data

    def test_change_password_does_not_log_out_the_current_session(self, authenticated_client, test_user):
        """Regression test: rotating the session token on password change
        (to invalidate any *other* active session, same reasoning as the
        forgot-password reset) must not also kill the session used to
        make the change itself — that would log someone out of their own
        account the moment they changed their own password. Checks a
        separate @login_required route afterward rather than trusting the
        flash message on the redirect target, since a flashed message can
        render on a login page too and wouldn't catch this on its own."""
        authenticated_client.post(
            "/auth/profile",
            data={
                "current_password": "TestPass123!",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
        )
        assert authenticated_client.get("/my-inquiries").status_code == 200

    def test_change_password_wrong_current(self, authenticated_client):
        """Test password change with wrong current password."""
        response = authenticated_client.post(
            "/auth/profile",
            data={
                "current_password": "WrongPassword",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
            follow_redirects=True,
        )

        assert b"incorrect" in response.data

    def test_change_password_mismatch(self, authenticated_client):
        """Test password change with mismatched new passwords."""
        response = authenticated_client.post(
            "/auth/profile",
            data={
                "current_password": "TestPass123!",
                "new_password": "NewSecurePass123",
                "confirm_password": "DifferentPass123",
            },
        )

        assert response.status_code == 200
