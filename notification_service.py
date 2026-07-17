"""Helpers for creating in-app notifications for logged-in users.

Mirrors the pattern in email_service.py: small, focused functions that
the admin routes call after a state change. Notifications are skipped
entirely for guest inquiries (inquiry.user_id is None) since there's no
account to attach them to.
"""
from app import db
from models.inquiry_notification import InquiryNotification


def notify_inquiry_status_change(inquiry, message: str) -> None:
    """Queue an in-app notification for the inquiry's owner, if any.

    Does not commit — callers should commit alongside their own changes
    (e.g. the inquiry.status update) so both happen in one transaction.
    """
    if not inquiry.user_id:
        return
    notif = InquiryNotification(
        user_id=inquiry.user_id,
        inquiry_id=inquiry.id,
        message=message,
    )
    db.session.add(notif)