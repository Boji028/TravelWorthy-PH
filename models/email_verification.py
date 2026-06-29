"""Email verification token model for registration verification."""
from typing import Optional
from datetime import datetime, timezone, timedelta
from app import db
import secrets


class EmailVerificationToken(db.Model):
    """Email verification token for confirming user registration."""
    __tablename__ = 'email_verification_tokens'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token: str = db.Column(db.String(128), unique=True, nullable=False, index=True)
    email: str = db.Column(db.String(150), nullable=False)  # Store email for verification
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at: datetime = db.Column(db.DateTime, nullable=False, index=True)
    verified_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    is_used: bool = db.Column(db.Boolean, default=False, index=True)

    # Relationships
    user = db.relationship('User', backref='verification_tokens')

    def __repr__(self) -> str:
        return f'<EmailVerificationToken {self.email}>'

    @staticmethod
    def _aware(dt: Optional[datetime]) -> Optional[datetime]:
        """Normalize a datetime read back from the DB to timezone-aware UTC.

        `expires_at` is stored as a plain db.DateTime (no `timezone=True`),
        so after a commit (which expires/refreshes the object) or any fresh
        query, SQLAlchemy hands back a naive datetime on both SQLite and
        Postgres — even though it was written as tz-aware UTC. Comparing
        that naive value directly against `datetime.now(timezone.utc)`
        raises `TypeError: can't compare offset-naive and offset-aware
        datetimes`. Treat a naive value as UTC (which is what it always is
        here, since every write path uses `datetime.now(timezone.utc)`).
        """
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def generate_token(user_id: int, email: str, expires_in_hours: int = 24) -> 'EmailVerificationToken':
        """Generate a new verification token for a user.
        
        Args:
            user_id: User ID to verify
            email: Email address to verify
            expires_in_hours: Hours until token expires (default 24)
        
        Returns:
            EmailVerificationToken instance
        """
        token = secrets.token_urlsafe(64)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expires_in_hours)
        
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            email=email,
            expires_at=expires_at,
            is_used=False
        )
        
        return verification_token

    @staticmethod
    def get_valid_token(token: str) -> Optional['EmailVerificationToken']:
        """Get a valid (unused and not expired) verification token.
        
        Args:
            token: Token string to verify
        
        Returns:
            EmailVerificationToken if valid, None otherwise
        """
        now = datetime.now(timezone.utc)
        
        verification = EmailVerificationToken.query.filter_by(
            token=token,
            is_used=False
        ).first()
        
        if not verification:
            return None
        
        # Check if token has expired
        if EmailVerificationToken._aware(verification.expires_at) < now:
            return None
        
        return verification

    def verify(self) -> bool:
        """Mark token as used and verified.
        
        Returns:
            True if verification successful
        """
        if self.is_used:
            return False
        
        if self._aware(self.expires_at) < datetime.now(timezone.utc):
            return False    
        
        self.is_used = True
        self.verified_at = datetime.now(timezone.utc)
        
        return True

    def is_valid(self) -> bool:
        """Check if token is still valid.
        
        Returns:
            True if token is valid (not used and not expired)
        """
        if self.is_used:
            return False
        
        if self.expires_at < datetime.now(timezone.utc):
            return False
        
        return True

    def is_expired(self) -> bool:
        """Check if token has expired.
        
        Returns:
            True if token has expired
        """
        return self._aware(self.expires_at) < datetime.now(timezone.utc)
