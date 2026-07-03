"""Application-wide constants and enums."""
from enum import Enum


class InquiryStatus(Enum):
    """Inquiry status constants."""

    NEW: str = "new"
    CONTACTED: str = "contacted"
    CONFIRMED: str = "confirmed"
    CLOSED: str = "closed"


class UserRole(Enum):
    """User role constants."""

    ADMIN: str = "admin"
    USER: str = "user"
