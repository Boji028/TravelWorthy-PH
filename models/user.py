"""User model for authentication and profile management."""
from typing import Optional
from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone


@login_manager.user_loader
def load_user(user_id: str) -> Optional['User']:
    """Load user from database by ID.
    
    Args:
        user_id: User ID string from session
        
    Returns:
        User object or None if not found
    """
    return db.session.get(User, int(user_id))


class User(db.Model, UserMixin):
    """User account model for authentication and profile data."""
    __tablename__ = 'users'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    email: str = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password: str = db.Column(db.String(200), nullable=False)
    phone: Optional[str] = db.Column(db.String(20), nullable=True)
    is_admin: bool = db.Column(db.Boolean, default=False, index=True)
    email_verified: bool = db.Column(db.Boolean, default=False, index=True)
    email_verified_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships - no type hint on relationships to avoid SQLAlchemy 2.0 conflicts
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def __repr__(self) -> str:
        return f'<User {self.email}>'
