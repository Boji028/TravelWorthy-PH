"""Subscriber model for the marketing newsletter opt-in list.

Deliberately separate from User — a Subscriber is not an account, has
no password, and never logs in. It only exists to back the "Subscribe"
box (name + email) that replaces full account registration.
"""
from datetime import datetime, timezone
from app import db


class Subscriber(db.Model):
    """A newsletter subscriber captured from the public Subscribe box."""

    __tablename__ = "subscribers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    subscribed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Subscriber {self.email}>"
