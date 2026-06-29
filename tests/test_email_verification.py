"""Tests for email verification functionality."""
import os
import pytest
from datetime import datetime, timezone, timedelta
from models.user import User
from models.email_verification import EmailVerificationToken
from email_verification_service import EmailVerificationService


class TestEmailVerificationConfig:
    """Test REQUIRE_EMAIL_VERIFICATION app configuration."""

    def test_verification_default_off_outside_production(self, monkeypatch):
        """Verification should default to off in non-production environments."""
        monkeypatch.delenv('REQUIRE_EMAIL_VERIFICATION', raising=False)
        monkeypatch.setenv('FLASK_ENV', 'development')
        monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
        monkeypatch.setenv('ADMIN_EMAIL', 'admin@test.com')
        monkeypatch.setenv('ADMIN_PASSWORD', 'TestPass123')

        from app import create_app
        app = create_app()
        assert app.config['REQUIRE_EMAIL_VERIFICATION'] is False

    def test_verification_default_on_in_production(self, monkeypatch):
        """Verification should default to on when FLASK_ENV=production."""
        monkeypatch.delenv('REQUIRE_EMAIL_VERIFICATION', raising=False)
        monkeypatch.setenv('FLASK_ENV', 'production')
        monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
        monkeypatch.setenv('ADMIN_EMAIL', 'admin@test.com')
        monkeypatch.setenv('ADMIN_PASSWORD', 'TestPass123')

        from app import create_app
        app = create_app()
        assert app.config['REQUIRE_EMAIL_VERIFICATION'] is True

    def test_verification_env_override(self, monkeypatch):
        """Explicit REQUIRE_EMAIL_VERIFICATION should override the default."""
        monkeypatch.setenv('REQUIRE_EMAIL_VERIFICATION', 'true')
        monkeypatch.setenv('FLASK_ENV', 'development')
        monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
        monkeypatch.setenv('ADMIN_EMAIL', 'admin@test.com')
        monkeypatch.setenv('ADMIN_PASSWORD', 'TestPass123')

        from app import create_app
        app = create_app()
        assert app.config['REQUIRE_EMAIL_VERIFICATION'] is True


class TestEmailVerificationToken:
    """Test EmailVerificationToken model."""

    def test_generate_token(self, test_user):
        """Test token generation."""
        token = EmailVerificationToken.generate_token(test_user.id, test_user.email)

        assert token.user_id == test_user.id
        assert token.email == test_user.email
        assert token.token is not None
        assert len(token.token) > 0
        assert token.is_used == False
        assert token.verified_at is None

    def test_token_expiration(self, test_user, app):
        """Test token expiration check."""
        # Create token that expires in 1 hour
        token_obj = EmailVerificationToken.generate_token(
            test_user.id,
            test_user.email,
            expires_in_hours=1
        )

        assert token_obj.is_valid() == True

        # Manually set expiration to past
        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        assert token_obj.is_valid() == False
        assert token_obj.is_expired() == True

    def test_get_valid_token(self, test_user, app):
        """Test retrieving a valid token."""
        token_obj = EmailVerificationToken.generate_token(
            test_user.id,
            test_user.email
        )
        from app import db
        db.session.add(token_obj)
        db.session.commit()

        retrieved = EmailVerificationToken.get_valid_token(token_obj.token)
        assert retrieved is not None
        assert retrieved.user_id == test_user.id

    def test_get_invalid_token(self, app):
        """Test retrieving an invalid token."""
        retrieved = EmailVerificationToken.get_valid_token('invalid_token')
        assert retrieved is None

    def test_verify_token(self, test_user, app):
        """Test token verification."""
        token_obj = EmailVerificationToken.generate_token(
            test_user.id,
            test_user.email
        )
        from app import db
        db.session.add(token_obj)
        db.session.commit()

        # Verify the token
        result = token_obj.verify()
        assert result == True
        assert token_obj.is_used == True
        assert token_obj.verified_at is not None

    def test_verify_already_used_token(self, test_user, app):
        """Test verifying an already used token."""
        token_obj = EmailVerificationToken.generate_token(
            test_user.id,
            test_user.email
        )
        from app import db
        db.session.add(token_obj)
        db.session.commit()

        # Verify once
        token_obj.verify()
        db.session.commit()

        # Try to verify again
        result = token_obj.verify()
        assert result == False


class TestEmailVerificationService:
    """Test EmailVerificationService."""

    def test_create_verification_token(self, test_user, app):
        """Test creating a verification token."""
        token = EmailVerificationService.create_verification_token(
            test_user.id,
            test_user.email
        )

        assert token is not None
        assert len(token) > 0

    def test_create_verification_token_invalid_user(self, app):
        """Test creating token for non-existent user."""
        with pytest.raises(ValueError):
            EmailVerificationService.create_verification_token(
                9999,
                'invalid@example.com'
            )

    def test_verify_email_success(self, test_user, app):
        """Test successful email verification."""
        token = EmailVerificationService.create_verification_token(
            test_user.id,
            test_user.email
        )

        success, message, user = EmailVerificationService.verify_email(token)

        assert success == True
        assert user is not None
        assert user.id == test_user.id
        assert user.email_verified == True

    def test_verify_email_invalid_token(self, app):
        """Test email verification with invalid token."""
        success, message, user = EmailVerificationService.verify_email('invalid_token')

        assert success == False
        assert user is None

    def test_resend_verification_email_success(self, test_user, app, monkeypatch):
        """Test resending verification email."""
        # Mail is deliberately unconfigured in the test environment (conftest
        # blanks MAIL_USERNAME/PASSWORD to avoid real outbound SMTP during
        # tests), so the actual send always reports failure. Mock the send
        # boundary itself so this test verifies resend_verification_email's
        # own logic (token creation, success message) rather than real mail.
        monkeypatch.setattr(
            EmailVerificationService, 'send_verification_email',
            staticmethod(lambda *args, **kwargs: True)
        )

        # test_user fixture defaults to email_verified=True; reset it so
        # this hits the actual resend path instead of the already-verified branch.
        test_user.email_verified = False
        from app import db
        db.session.commit()

        success, message = EmailVerificationService.resend_verification_email(
            test_user.email
        )

        # Should succeed for unverified user
        assert success == True

    def test_resend_verification_email_already_verified(self, test_user, app):
        """Test resending to already verified email."""
        test_user.email_verified = True
        test_user.email_verified_at = datetime.now(timezone.utc)
        from app import db
        db.session.commit()

        success, message = EmailVerificationService.resend_verification_email(
            test_user.email
        )

        assert success == False

    def test_cleanup_expired_tokens(self, test_user, app):
        """Test cleaning up expired tokens."""
        from app import db

        # Create an expired token
        expired_token = EmailVerificationToken.generate_token(
            test_user.id,
            test_user.email,
            expires_in_hours=-1  # Already expired
        )
        db.session.add(expired_token)
        db.session.commit()

        # Create a valid token
        valid_token = EmailVerificationToken.generate_token(
            test_user.id,
            test_user.email,
            expires_in_hours=24
        )
        db.session.add(valid_token)
        db.session.commit()

        # Cleanup
        deleted_count = EmailVerificationService.cleanup_expired_tokens()

        assert deleted_count == 1

        # Check that valid token still exists
        remaining = EmailVerificationToken.query.filter_by(is_used=False).all()
        assert len(remaining) >= 1


class TestEmailVerificationRoutes:
    """Test email verification routes."""

    @pytest.fixture(autouse=True)
    def enable_email_verification(self, app):
        """Route tests assume verification is required."""
        app.config['REQUIRE_EMAIL_VERIFICATION'] = True

    def test_register_requires_email_verification(self, client):
        """Test that registration requires email verification."""
        response = client.post('/auth/register', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'phone': '+1234567890',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123'
        }, follow_redirects=True)

        assert response.status_code == 200

        # User should be created but not verified
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.email_verified == False

    def test_login_requires_email_verification(self, client, test_user):
        """Test that login requires email verification."""
        # Set user email as unverified
        test_user.email_verified = False
        from app import db
        db.session.commit()

        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'TestPass123!',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'verify your email' in response.data

    def test_login_with_verified_email(self, client, test_user):
        """Test login succeeds with verified email."""
        # Ensure user is verified
        test_user.email_verified = True
        from app import db
        db.session.commit()

        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'TestPass123!',
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to home or dashboard
        assert b'Welcome back' in response.data

    def test_verify_email_route(self, client, test_user, app):
        """Test email verification via route."""
        from email_verification_service import EmailVerificationService

        # Create verification token
        token = EmailVerificationService.create_verification_token(
            test_user.id,
            test_user.email
        )

        # Verify via route
        response = client.get(f'/auth/verify-email/{token}', follow_redirects=True)

        assert response.status_code == 200
        assert b'successfully' in response.data.lower()

        # Check that user is now verified
        user = User.query.get(test_user.id)
        assert user.email_verified == True

    def test_pending_verification_page(self, client):
        """Test pending verification page."""
        response = client.get('/auth/pending-verification?email=test@example.com')

        assert response.status_code == 200
        assert b'test@example.com' in response.data

    def test_resend_verification_route(self, client, test_user, monkeypatch):
        """Test resend verification route."""
        # See note in test_resend_verification_email_success — mail is
        # deliberately unconfigured in tests, so mock the send boundary.
        monkeypatch.setattr(
            EmailVerificationService, 'send_verification_email',
            staticmethod(lambda *args, **kwargs: True)
        )

        # Ensure user is not verified
        test_user.email_verified = False
        from app import db
        db.session.commit()

        response = client.post('/auth/resend-verification', data={
            'email': test_user.email
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show success or pending verification page
        assert b'pending' in response.data.lower() or b'sent' in response.data.lower()

    def test_resend_verification_invalid_email(self, client):
        """Test resend verification with non-existent email."""
        response = client.post('/auth/resend-verification', data={
            'email': 'nonexistent@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show success message (security: don't reveal if email exists)
        assert b'sent' in response.data.lower() or b'email' in response.data.lower()