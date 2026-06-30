"""In-app notification model for inquiry status updates.

Only created for inquiries linked to a logged-in user (inquiry.user_id
is set). Guest inquiries have no account to notify in-app — they still
get the existing email notifications, unaffected by this model.
"""
from datetime import datetime, timezone
from app import db


class InquiryNotification(db.Model):
    """A single notification event tied to one inquiry and one user."""
    __tablename__ = 'inquiry_notifications'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    inquiry_id: int = db.Column(db.Integer, db.ForeignKey('inquiries.id'), nullable=False, index=True)
    message: str = db.Column(db.String(255), nullable=False)
    is_read: bool = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship('User', backref=db.backref('inquiry_notifications', passive_deletes=True))
    inquiry = db.relationship('Inquiry', backref=db.backref('notifications', cascade='all, delete-orphan')) 

    def __repr__(self) -> str:
        return f'<InquiryNotification user={self.user_id} inquiry={self.inquiry_id} read={self.is_read}>'