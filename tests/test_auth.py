"""Tests for authentication routes.

Public registration is gone (see routes/auth.py) — staff accounts are
created via the admin panel now (tests/test_admin_users.py). This file
covers what's left: login, logout, and password change, all at their
new paths under /staff-portal, /logout, /profile.
"""
import pytest
from models.user import User
from werkzeug.security import check_password_hash


class TestUserLogin:
    """Test user login functionality."""

    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post(
            "/staff-portal", data={"email": test_user.email, "password": "TestPass123!"}, follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Welcome back" in response.data

    def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/staff-portal", data={"email": test_user.email, "password": "WrongPassword"}, follow_redirects=True
        )

        assert b"Invalid email or password" in response.data

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/staff-portal", data={"email": "nonexistent@example.com", "password": "TestPass123!"}, follow_redirects=True
        )

        assert b"Invalid email or password" in response.data

    def test_login_case_insensitive_email(self, client, test_user):
        """Test login with different email case."""
        response = client.post(
            "/staff-portal", data={"email": test_user.email.upper(), "password": "TestPass123!"}, follow_redirects=True
        )

        assert response.status_code == 200

    def test_login_page_views_are_not_rate_limited(self, client):
        """The rate limit is meant to throttle login-attempt POSTs only,
        not page views - matches the same fix already applied to
        forgot-password after it originally rate-limited GETs too."""
        for _ in range(7):
            response = client.get("/staff-portal")
            assert response.status_code == 200

    def test_repeated_failed_logins_get_rate_limited(self, client, test_user):
        """Six failed attempts for the same email within a minute should
        trip the 5-per-minute cap, slowing down password-guessing against
        a single account."""
        for _ in range(5):
            response = client.post(
                "/staff-portal", data={"email": test_user.email, "password": "WrongPassword"}, follow_redirects=True
            )
            assert response.status_code == 200

        response = client.post(
            "/staff-portal", data={"email": test_user.email, "password": "WrongPassword"}, follow_redirects=True
        )
        assert response.status_code == 429

    def test_login_rate_limit_is_keyed_by_email_not_shared_globally(self, client, test_user):
        """A flood of attempts against one email must not lock out a
        different visitor trying to log into a different account from
        the same test client/IP."""
        for _ in range(5):
            client.post("/staff-portal", data={"email": test_user.email, "password": "WrongPassword"})

        response = client.post(
            "/staff-portal", data={"email": "someone.else@example.com", "password": "WrongPassword"}
        )
        assert response.status_code != 429

    def test_login_does_not_crash_with_no_email_and_no_remote_addr(self, client):
        """Same class of bug already fixed on forgot-password's key_func -
        a request with neither an email field nor a remote_addr must not
        crash with an uncaught AttributeError before the route even runs."""
        response = client.post(
            "/staff-portal",
            data={},
            environ_overrides={"REMOTE_ADDR": None},
        )
        assert response.status_code != 500


class TestUserLogout:
    """Test user logout functionality."""

    def test_logout(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.get("/logout", follow_redirects=True)

        assert response.status_code == 200
        assert b"logged out" in response.data


class TestPasswordChange:
    """Test password change functionality."""

    def test_change_password_success(self, authenticated_client, test_user):
        """Test successful password change."""
        response = authenticated_client.post(
            "/profile",
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
            "/profile",
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
            "/profile",
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
            "/profile",
            data={
                "current_password": "TestPass123!",
                "new_password": "NewSecurePass123",
                "confirm_password": "DifferentPass123",
            },
        )

        assert response.status_code == 200
