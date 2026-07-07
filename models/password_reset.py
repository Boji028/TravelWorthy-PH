"""Password reset token model for the forgot-password flow."""
from typing import Optional
from datetime import datetime, timezone, timedelta
from app import db
import secrets


class PasswordResetToken(db.Model):
    """Single-use, expiring token for resetting a forgotten password."""

    __tablename__ = "password_reset_tokens"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token: str = db.Column(db.String(128), unique=True, nullable=False, index=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at: datetime = db.Column(db.DateTime, nullable=False, index=True)
    used_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    is_used: bool = db.Column(db.Boolean, default=False, index=True)

    user = db.relationship("User", backref="password_reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id}>"

    @staticmethod
    def _aware(dt: Optional[datetime]) -> Optional[datetime]:
        """Normalize a datetime read back from the DB to timezone-aware UTC.

        Same reasoning as EmailVerificationToken._aware: expires_at is
        stored as a plain db.DateTime, so SQLAlchemy hands back a naive
        datetime after a commit or fresh query even though it was written
        as tz-aware UTC. Treat naive as UTC since every write path uses
        datetime.now(timezone.utc).
        """
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def generate_token(user_id: int, expires_in_hours: int = 1) -> "PasswordResetToken":
        """Generate a new password reset token for a user.

        Args:
            user_id: User ID requesting the reset
            expires_in_hours: Hours until token expires (default 1 — shorter
                than email verification since this is more security-sensitive)

        Returns:
            PasswordResetToken instance
        """
        token = secrets.token_urlsafe(64)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expires_in_hours)

        return PasswordResetToken(user_id=user_id, token=token, expires_at=expires_at, is_used=False)

    @staticmethod
    def get_valid_token(token: str) -> Optional["PasswordResetToken"]:
        """Get a valid (unused and not expired) reset token.

        Args:
            token: Token string to look up

        Returns:
            PasswordResetToken if valid, None otherwise
        """
        now = datetime.now(timezone.utc)

        reset_token = PasswordResetToken.query.filter_by(token=token, is_used=False).first()

        if not reset_token:
            return None

        if PasswordResetToken._aware(reset_token.expires_at) < now:
            return None

        return reset_token

    def consume(self) -> bool:
        """Mark this token as used. Returns False if already used or expired."""
        if self.is_used:
            return False

        if self._aware(self.expires_at) < datetime.now(timezone.utc):
            return False

        self.is_used = True
        self.used_at = datetime.now(timezone.utc)

        return True

    def is_valid(self) -> bool:
        """Check if token is still valid (not used and not expired)."""
        if self.is_used:
            return False

        if self._aware(self.expires_at) < datetime.now(timezone.utc):
            return False

        return True
