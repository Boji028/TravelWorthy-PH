"""Email verification service for handling verification workflows."""
from typing import Optional, Tuple
from datetime import datetime, timezone
from flask import url_for
from flask_mail import Message
from app import db, mail
from models.email_verification import EmailVerificationToken
from models.user import User
from logging_service import StructuredLogger


class EmailVerificationService:
    """Service for managing email verification workflows."""

    @staticmethod
    def create_verification_token(user_id: int, email: str, expires_in_hours: int = 24) -> str:
        """Create a verification token for a user.
        
        Args:
            user_id: User ID to create token for
            email: Email address to verify
            expires_in_hours: Hours until token expires
        
        Returns:
            Token string
        
        Raises:
            ValueError: If user not found
        """
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Invalidate any previous tokens for this user
            EmailVerificationToken.query.filter_by(user_id=user_id, is_used=False).update(
                {'is_used': True}
            )
            db.session.commit()
            
            # Create new token
            token_obj = EmailVerificationToken.generate_token(user_id, email, expires_in_hours)
            db.session.add(token_obj)
            db.session.commit()
            
            StructuredLogger.log_auth_event(
                'verification_token_created',
                email,
                True,
                reason=f"Verification token created for user {user_id}"
            )
            
            return token_obj.token
        
        except Exception as e:
            StructuredLogger.log_error(
                'email_verification',
                f"Failed to create verification token: {str(e)}",
                {'user_id': user_id, 'email': email},
                'ERROR'
            )
            raise

    @staticmethod
    def send_verification_email(user_email: str, user_name: str, token: str, is_resend: bool = False) -> bool:
        """Send verification email to user.
        
        Args:
            user_email: Email address to send to
            user_name: User's name for greeting
            token: Verification token
            is_resend: True if this is a resend
        
        Returns:
            True if email sent successfully
        """
        try:
            # Build verification URL
            verification_url = url_for('auth.verify_email', token=token, _external=True)
            
            subject = "Re-verify Your Email" if is_resend else "Verify Your Email Address"
            
            # Email body
            body = f"""Dear {user_name},

{"Thank you for requesting a new verification link. " if is_resend else "Thank you for registering with our Travel Agency!"}

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you did not create this account, please ignore this email.

Best regards,
Travel Agency Team"""
            
            html_body = f"""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <p>Dear {user_name},</p>
    <p>{"Thank you for requesting a new verification link." if is_resend else "Thank you for registering with our Travel Agency!"}</p>
    <p>Please verify your email address by clicking the button below:</p>
    <p>
        <a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
            Verify Email
        </a>
    </p>
    <p>Or copy and paste this link: <a href="{verification_url}">{verification_url}</a></p>
    <p style="color: #666; font-size: 12px;">This link will expire in 24 hours.</p>
    <p style="color: #666; font-size: 12px;">If you did not create this account, please ignore this email.</p>
    <p>Best regards,<br>Travel Agency Team</p>
</body>
</html>"""
            
            message = Message(
                subject=subject,
                recipients=[user_email],
                body=body,
                html=html_body
            )
            
            mail.send(message)
            
            StructuredLogger.log_auth_event(
                'verification_email_sent',
                user_email,
                True,
                reason=f"Verification email sent ({'resend' if is_resend else 'initial'})"
            )
            
            return True
        
        except Exception as e:
            StructuredLogger.log_error(
                'email_verification',
                f"Failed to send verification email: {str(e)}",
                {'email': user_email},
                'ERROR'
            )
            return False

    @staticmethod
    def verify_email(token: str) -> Tuple[bool, str, Optional[User]]:
        """Verify email with token.
        
        Args:
            token: Verification token
        
        Returns:
            Tuple of (success: bool, message: str, user: User or None)
        """
        try:
            # Get token from database
            token_obj = EmailVerificationToken.get_valid_token(token)
            
            if not token_obj:
                return False, "Invalid or expired verification link", None
            
            # Get user
            user = User.query.get(token_obj.user_id)
            if not user:
                return False, "User not found", None
            
            # Mark email as verified
            user.email_verified = True
            user.email_verified_at = datetime.now(timezone.utc)
            
            # Mark token as used
            token_obj.verify()
            
            db.session.commit()
            
            StructuredLogger.log_auth_event(
                'email_verified',
                user.email,
                True,
                reason="Email successfully verified"
            )
            
            return True, "Email verified successfully! You can now log in.", user
        
        except Exception as e:
            StructuredLogger.log_error(
                'email_verification',
                f"Failed to verify email: {str(e)}",
                {'token': token[:20] + '...'},  # Don't log full token
                'ERROR'
            )
            return False, "An error occurred during verification. Please try again.", None

    @staticmethod
    def resend_verification_email(email: str) -> Tuple[bool, str]:
        """Resend verification email to user.
        
        Args:
            email: User's email address
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Don't reveal if user exists (security)
                return True, "If an account with this email exists, a verification link has been sent."
            
            # Check if already verified
            if user.email_verified:
                return False, "This email is already verified. Please log in."
            
            # Create new token
            token = EmailVerificationService.create_verification_token(
                user.id,
                user.email,
                expires_in_hours=24
            )
            
            # Send email
            if not EmailVerificationService.send_verification_email(
                user.email,
                user.name,
                token,
                is_resend=True
            ):
                return False, "Failed to send verification email. Please try again later."
            
            return True, "Verification email sent successfully!"
        
        except Exception as e:
            StructuredLogger.log_error(
                'email_verification',
                f"Failed to resend verification email: {str(e)}",
                {'email': email},
                'ERROR'
            )
            return False, "An error occurred. Please try again later."

    @staticmethod
    def cleanup_expired_tokens() -> int:
        """Clean up expired verification tokens.
        
        Returns:
            Number of tokens deleted
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Delete expired and used tokens
            result = EmailVerificationToken.query.filter(
                EmailVerificationToken.expires_at < now,
                EmailVerificationToken.is_used == False
            ).delete()
            
            db.session.commit()
            
            StructuredLogger.log_admin_action(
                'cleanup',
                'email_verification_tokens',
                None,
                {'tokens_deleted': result}
            )
            
            return result
        
        except Exception as e:
            StructuredLogger.log_error(
                'email_verification',
                f"Failed to cleanup expired tokens: {str(e)}",
                {},
                'ERROR'
            )
            return 0
