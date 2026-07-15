"""User model for authentication and profile management."""
import secrets
from typing import Optional
from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone


@login_manager.user_loader
def load_user(user_id: str) -> Optional["User"]:
    """Load user from database by ID.

    user_id is normally "<id>:<session_token>" (see User.get_id()) — the
    token half lets a password reset invalidate every other session for
    that account, since a stale session's embedded token no longer
    matches the current one and this returns None (Flask-Login treats
    that as logged out). A bare numeric id with no ":" is also accepted:
    that's a session cookie issued before this feature existed, and
    honoring it once — rather than force-logging out every already-signed-in
    user the moment this deploys — is a deliberate choice, not an
    oversight. Those sessions upgrade to the token-aware format the next
    time that user actually logs in again.

    Args:
        user_id: User ID string from session, from User.get_id()

    Returns:
        User object or None if not found, or if a token was present and
        didn't match (session predates a password reset/change).
    """
    if ":" in user_id:
        raw_id, _, token = user_id.partition(":")
    else:
        raw_id, token = user_id, None

    try:
        user = db.session.get(User, int(raw_id))
    except (ValueError, TypeError):
        return None
    if user is None:
        return None
    if token is not None and user.session_token and token != user.session_token:
        return None

    return user


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
    # Nullable and lazily generated (see get_id()) rather than backfilled
    # by migration — every user gets one the next time they log in
    # regardless, so a data-backfill migration isn't needed. Rotated by
    # rotate_session_token() on password reset/change to invalidate any
    # other active session for the account.
    session_token: Optional[str] = db.Column(db.String(32), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def get_id(self) -> str:
        """Flask-Login calls this to decide what to store in the session
        cookie. Embedding session_token (generating one on first use if
        this account doesn't have one yet) means a stale cookie stops
        working the moment the token is rotated, without needing to
        track/revoke sessions server-side."""
        if not self.session_token:
            self.session_token = secrets.token_hex(16)
            db.session.commit()
        return f"{self.id}:{self.session_token}"

    def rotate_session_token(self) -> None:
        """Invalidate every other active session for this account by
        replacing session_token — any cookie carrying the old value stops
        authenticating on its next request. Does not commit; caller
        commits alongside the password change itself."""
        self.session_token = secrets.token_hex(16)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
