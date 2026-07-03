"""Tour package model for travel offerings."""
from typing import Optional
from datetime import datetime, timezone
from app import db


class TourPackage(db.Model):
    """Tour package model for travel destinations."""

    __tablename__ = "tour_packages"

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(200), nullable=False)
    description: str = db.Column(db.Text, nullable=False)
    destination: str = db.Column(db.String(150), nullable=False)
    country_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("countries.id"), nullable=True, index=True)
    duration_days: int = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    currency: str = db.Column(db.String(10), default="PHP")
    image: Optional[str] = db.Column(db.String(300), nullable=True, default="default_tour.jpg")
    image_size_kb: Optional[float] = db.Column(db.Float, nullable=True)  # Track image size (KB)
    image_uploaded_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)  # Track upload time
    flier_image: Optional[str] = db.Column(db.String(300), nullable=True)  # Separate promotional flier image
    flier_image_size_kb: Optional[float] = db.Column(db.Float, nullable=True)
    flier_image_uploaded_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    inclusions: Optional[str] = db.Column(db.Text, nullable=True)
    exclusions: Optional[str] = db.Column(db.Text, nullable=True)
    is_active: bool = db.Column(db.Boolean, default=True, index=True)
    is_featured: bool = db.Column(db.Boolean, default=False, index=True)
    package_type: str = db.Column(db.String(20), default="domestic", nullable=False, index=True)
    assigned_agent_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("agents.id"), nullable=True, index=True)
    amenities: Optional[str] = db.Column(db.Text, nullable=True)
    location_description: Optional[str] = db.Column(db.Text, nullable=True)
    latitude: Optional[float] = db.Column(db.Float, nullable=True)
    longitude: Optional[float] = db.Column(db.Float, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships - no type hint to avoid SQLAlchemy 2.0 conflicts
    images = db.relationship(
        "PackageImage", backref="package", lazy=True, order_by="PackageImage.order", cascade="all, delete-orphan"
    )
    assigned_agent = db.relationship("Agent", backref="packages")

    def __repr__(self) -> str:
        return f"<TourPackage {self.title}>"
