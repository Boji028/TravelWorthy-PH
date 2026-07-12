"""In-app notification model for inquiry status updates.

Only created for inquiries linked to a logged-in user (inquiry.user_id
is set). Guest inquiries have no account to notify in-app — they still
get the existing email notifications, unaffected by this model.

inquiry_id is nullable: a system-wide notification (e.g. "N inquiries
will be auto-deleted soon", or "new package added") isn't about any
one inquiry, so it carries inquiry_id=None. Callers rendering a
notification must check `notification.inquiry` for None before
accessing it.

link_url is an optional override for where the notification should
link to. It exists specifically for system-wide notifications
(inquiry_id=None) that aren't admin inquiry-related — without it, the
template has no way to know whether an inquiry_id=None notification
should go to the admin inquiries list (e.g. an expiry warning) or
somewhere else entirely (e.g. a new package's detail page). Existing
notification types (inquiry status/creation, admin new-inquiry alerts,
expiry warnings) leave this null and keep working exactly as before —
the template falls back to its original inquiry-id-based logic when
link_url isn't set.
"""
from datetime import datetime, timezone
from app import db


class InquiryNotification(db.Model):
    """A single notification event for one user, optionally tied to one inquiry."""

    __tablename__ = "inquiry_notifications"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    inquiry_id: int = db.Column(db.Integer, db.ForeignKey("inquiries.id"), nullable=True, index=True)
    message: str = db.Column(db.String(255), nullable=False)
    link_url: str = db.Column(db.String(255), nullable=True)
    is_read: bool = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship("User", backref=db.backref("inquiry_notifications", passive_deletes=True))
    inquiry = db.relationship("Inquiry", backref=db.backref("notifications", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<InquiryNotification user={self.user_id} inquiry={self.inquiry_id} read={self.is_read}>"
