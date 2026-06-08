"""Application-wide constants and enums."""
from enum import Enum


class BookingStatus(Enum):
    """Booking status constants."""
    PENDING: str = 'pending'
    CONFIRMED: str = 'confirmed'
    CANCELLED: str = 'cancelled'


class InquiryStatus(Enum):
    """Inquiry status constants."""
    NEW: str = 'new'
    CONTACTED: str = 'contacted'
    CLOSED: str = 'closed'


class UserRole(Enum):
    """User role constants."""
    ADMIN: str = 'admin'
    USER: str = 'user'
