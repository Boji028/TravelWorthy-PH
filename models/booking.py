"""Booking model for tour package reservations."""
from typing import Optional
from datetime import datetime, date, timezone
from app import db


class Booking(db.Model):
    """Tour booking model tracking reservations."""
    __tablename__ = 'bookings'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    package_id: int = db.Column(db.Integer, db.ForeignKey('tour_packages.id'), nullable=False, index=True)
    contact_number: Optional[str] = db.Column(db.String(20), nullable=True)
    num_travelers: int = db.Column(db.Integer, nullable=False, default=1)
    travel_date: date = db.Column(db.Date, nullable=False)
    end_travel_date: Optional[date] = db.Column(db.Date, nullable=True)
    total_price: float = db.Column(db.Float, nullable=False)
    special_requests: Optional[str] = db.Column(db.Text, nullable=True)
    status: str = db.Column(db.String(20), default='pending', index=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # No explicit relationship here — Booking.package is created automatically
    # by the backref='package' on TourPackage.bookings (see models/package.py).
    # Use joinedload(Booking.package) in queries that need package data.

    def __repr__(self) -> str:
        return f'<Booking {self.id} - {self.status}>'
