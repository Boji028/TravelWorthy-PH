"""Tour package model for travel offerings."""
from typing import Optional
from datetime import datetime, timezone
from app import db


class TourPackage(db.Model):
    """Tour package model for travel destinations and bookings."""
    __tablename__ = 'tour_packages'

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(200), nullable=False)
    description: str = db.Column(db.Text, nullable=False)
    destination: str = db.Column(db.String(150), nullable=False)
    country_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=True, index=True)
    duration_days: int = db.Column(db.Integer, nullable=False)
    price: float = db.Column(db.Float, nullable=False)
    currency: str = db.Column(db.String(10), default='PHP')
    max_slots: int = db.Column(db.Integer, nullable=False, default=20)
    available_slots: int = db.Column(db.Integer, nullable=False, default=20)
    image: Optional[str] = db.Column(db.String(300), nullable=True, default='default_tour.jpg')
    image_size_kb: Optional[float] = db.Column(db.Float, nullable=True)  # Track image size (KB)
    image_uploaded_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)  # Track upload time
    inclusions: Optional[str] = db.Column(db.Text, nullable=True)
    exclusions: Optional[str] = db.Column(db.Text, nullable=True)
    is_active: bool = db.Column(db.Boolean, default=True, index=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships - no type hint to avoid SQLAlchemy 2.0 conflicts
    bookings = db.relationship('Booking', backref='package', lazy=True)

    def __repr__(self) -> str:
        return f'<TourPackage {self.title}>'
