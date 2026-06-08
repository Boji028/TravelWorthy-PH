"""Inquiry model for tour inquiry requests."""
from typing import Optional
from datetime import datetime, date, timezone
import secrets
from app import db


class Inquiry(db.Model):
    """Trip inquiry model for custom tour requests."""
    __tablename__ = 'inquiries'

    id: int = db.Column(db.Integer, primary_key=True)
    reference_number: str = db.Column(db.String(20), unique=True, nullable=False, index=True)
    package_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('tour_packages.id'), nullable=True)
    name: str = db.Column(db.String(100), nullable=False)
    email: str = db.Column(db.String(120), nullable=False)
    contact_number: str = db.Column(db.String(20), nullable=False)
    destination: str = db.Column(db.String(200), nullable=False)
    travel_date_from: date = db.Column(db.Date, nullable=False)
    travel_date_to: date = db.Column(db.Date, nullable=False)
    num_adults: int = db.Column(db.Integer, nullable=False, default=1)
    num_children: int = db.Column(db.Integer, nullable=False, default=0)
    num_infants: int = db.Column(db.Integer, nullable=False, default=0)
    special_requests: Optional[str] = db.Column(db.Text, nullable=True)
    status: str = db.Column(db.String(20), default='new', index=True)
    inquiry_type: str = db.Column(db.String(20), default='general')
    admin_response: Optional[str] = db.Column(db.Text, nullable=True)
    responded_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships - no type hint to avoid SQLAlchemy 2.0 conflicts
    package = db.relationship('TourPackage', backref='inquiries')

    def __init__(self, **kwargs):
        """Initialize with auto-generated reference number."""
        super().__init__(**kwargs)
        if not self.reference_number:
            # Generate human-readable reference: INQ-XXXXX
            self.reference_number = self._generate_reference()

    @staticmethod
    def _generate_reference() -> str:
        """Generate unique reference number like INQ-000123."""
        # Use random suffix to ensure uniqueness
        while True:
            suffix = secrets.token_hex(3).upper()[:5]  # 5 hex chars = ~1M combinations
            ref = f"INQ-{suffix}"
            # Check if already exists
            if not db.session.query(Inquiry).filter_by(reference_number=ref).first():
                return ref

    @property
    def total_pax(self) -> int:
        """Calculate total number of travelers."""
        return self.num_adults + self.num_children + self.num_infants

    def __repr__(self) -> str:
        return f'<Inquiry {self.reference_number} - {self.name}>'
