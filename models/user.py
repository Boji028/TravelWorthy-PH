"""User model for authentication and profile management."""
from typing import Optional
from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone


@login_manager.user_loader
def load_user(user_id: str) -> Optional["User"]:
    """Load user from database by ID.

    Args:
        user_id: User ID string from session

    Returns:
        User object or None if not found
    """
    return db.session.get(User, int(user_id))


class User(db.Model, UserMixin):
    """User account model for authentication and profile data."""

    __tablename__ = "users"
    __table_args__ = (db.UniqueConstraint("oauth_provider", "oauth_id", name="uq_users_oauth_identity"),)

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    email: str = db.Column(db.String(150), unique=True, nullable=False, index=True)
    # Nullable: OAuth-only accounts (Google) never set a password.
    password: Optional[str] = db.Column(db.String(200), nullable=True)
    phone: Optional[str] = db.Column(db.String(20), nullable=True)
    is_admin: bool = db.Column(db.Boolean, default=False, index=True)
    email_verified: bool = db.Column(db.Boolean, default=False, index=True)
    email_verified_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    # 'google' | None (None = normal email/password account)
    oauth_provider: Optional[str] = db.Column(db.String(20), nullable=True, index=True)
    oauth_id: Optional[str] = db.Column(db.String(255), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<User {self.email}>"
