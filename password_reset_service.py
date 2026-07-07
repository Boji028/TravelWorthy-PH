"""Password reset service for handling the forgot-password workflow."""
from typing import Optional, Tuple
from flask import url_for, current_app
from flask_mail import Message
from werkzeug.security import generate_password_hash
from app import db, mail
from models.password_reset import PasswordResetToken
from models.user import User
from logging_service import StructuredLogger


class PasswordResetService:
    """Service for managing the forgot-password / reset-password workflow."""

    @staticmethod
    def request_reset(email: str) -> Tuple[bool, str]:
        """Start a password reset for the given email, if eligible.

        Always returns a generic success message regardless of whether the
        email exists, to avoid leaking which emails are registered.

        Args:
            email: Email address submitted on the forgot-password form

        Returns:
            Tuple of (success: bool, message: str)
        """
        generic_message = "If an account with this email exists, a password reset link has been sent."

        try:
            user = User.query.filter_by(email=email).first()

            if not user:
                return True, generic_message

            if not user.password:
                # Google-only account — there is no password to reset.
                StructuredLogger.log_auth_event(
                    "password_reset_skipped_oauth", email, True, reason="Account is Google-only, no password to reset"
                )
                return True, generic_message

            # Invalidate any previous unused tokens for this user.
            PasswordResetToken.query.filter_by(user_id=user.id, is_used=False).update({"is_used": True})

            token_obj = PasswordResetToken.generate_token(user.id, expires_in_hours=1)
            db.session.add(token_obj)
            db.session.commit()

            if not PasswordResetService._send_reset_email(user.email, user.name, token_obj.token):
                return False, "Failed to send reset email. Please try again later."

            StructuredLogger.log_auth_event("password_reset_requested", email, True, reason="Reset token created")

            return True, generic_message

        except Exception as e:
            StructuredLogger.log_error("password_reset", f"Failed to request password reset: {str(e)}", {"email": email}, "ERROR")
            return False, "An error occurred. Please try again later."

    @staticmethod
    def _send_reset_email(user_email: str, user_name: str, token: str, expires_in_hours: int = 1) -> bool:
        """Send the password reset email. Returns True if sent successfully."""
        try:
            if not current_app.config.get("MAIL_USERNAME"):
                StructuredLogger.log_error(
                    "password_reset", "Mail not configured — reset email skipped", {"email": user_email}, "WARNING"
                )
                return False

            reset_url = url_for("auth.reset_password", token=token, _external=True)

            subject = "Reset Your Password"

            body = f"""Dear {user_name},

We received a request to reset your password. Click the link below to choose a new one:

{reset_url}

This link will expire in {expires_in_hours} hour(s).

If you did not request this, you can safely ignore this email — your password will not be changed.

Best regards,
Travel Worthy PH Team"""

            html_body = f"""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <p>Dear {user_name},</p>
    <p>We received a request to reset your password. Click the button below to choose a new one:</p>
    <p>
        <a href="{reset_url}" style="background-color: #175867; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
            Reset Password
        </a>
    </p>
    <p>Or copy and paste this link: <a href="{reset_url}">{reset_url}</a></p>
    <p style="color: #666; font-size: 12px;">This link will expire in {expires_in_hours} hour(s).</p>
    <p style="color: #666; font-size: 12px;">If you did not request this, you can safely ignore this email — your password will not be changed.</p>
    <p>Best regards,<br>Travel Worthy PH Team</p>
</body>
</html>"""

            message = Message(subject=subject, recipients=[user_email], body=body, html=html_body)
            mail.send(message)

            StructuredLogger.log_auth_event("password_reset_email_sent", user_email, True, reason="Reset email sent")

            return True

        except Exception as e:
            StructuredLogger.log_error("password_reset", f"Failed to send reset email: {str(e)}", {"email": user_email}, "ERROR")
            return False

    @staticmethod
    def reset_password(token: str, new_password: str) -> Tuple[bool, str, Optional[User]]:
        """Complete a password reset given a valid token and new password.

        Args:
            token: Reset token from the emailed link
            new_password: The new plaintext password to set

        Returns:
            Tuple of (success: bool, message: str, user: User or None)
        """
        try:
            token_obj = PasswordResetToken.get_valid_token(token)

            if not token_obj:
                return False, "This reset link is invalid or has expired. Please request a new one.", None

            user = db.session.get(User, token_obj.user_id)
            if not user:
                return False, "User not found.", None

            user.password = generate_password_hash(new_password)
            token_obj.consume()

            db.session.commit()

            StructuredLogger.log_auth_event("password_reset_completed", user.email, True, reason="Password reset via token")

            return True, "Your password has been reset. You can now log in.", user

        except Exception as e:
            StructuredLogger.log_error(
                "password_reset", f"Failed to reset password: {str(e)}", {"token": token[:20] + "..."}, "ERROR"
            )
            return False, "An error occurred while resetting your password. Please try again.", None
