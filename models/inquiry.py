"""Inquiry model for tour inquiry requests."""
from typing import Optional
from datetime import datetime, date, timezone
import secrets
from sqlalchemy.orm import validates
from app import db


class Inquiry(db.Model):
    """Trip inquiry model for custom tour requests."""

    __tablename__ = "inquiries"

    VALID_STATUSES = frozenset({"new", "contacted", "confirmed", "closed"})
    id: int = db.Column(db.Integer, primary_key=True)
    reference_number: str = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    package_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=True)
    name: str = db.Column(db.String(100), nullable=False)
    email: str = db.Column(db.String(120), nullable=False, index=True)
    contact_number: str = db.Column(db.String(20), nullable=False)
    destination: str = db.Column(db.String(200), nullable=False)
    travel_date_from: date = db.Column(db.Date, nullable=False)
    travel_date_to: date = db.Column(db.Date, nullable=False)
    num_adults: int = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    num_children: int = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    num_infants: int = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    special_requests: Optional[str] = db.Column(db.Text, nullable=True)
    status: str = db.Column(db.String(20), default="new", index=True, nullable=False)
    inquiry_type: str = db.Column(db.String(20), default="general")
    admin_response: Optional[str] = db.Column(db.Text, nullable=True)
    responded_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        db.CheckConstraint("travel_date_to >= travel_date_from", name="ck_inquiry_date_range"),
        db.CheckConstraint("num_adults >= 1", name="ck_inquiry_min_adults"),
        db.CheckConstraint("num_children >= 0", name="ck_inquiry_min_children"),
        db.CheckConstraint("num_infants >= 0", name="ck_inquiry_min_infants"),
    )

    package = db.relationship("TourPackage", backref="inquiries")
    user = db.relationship("User", backref="inquiries")

    def __init__(self, **kwargs):
        """Initialize with auto-generated reference number."""
        super().__init__(**kwargs)
        if not self.reference_number:
            self.reference_number = self._generate_reference()

    @validates("status")
    def validate_status(self, key, value):
        if value not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{value}'. Allowed: {self.VALID_STATUSES}")
        return value

    @staticmethod
    def _generate_reference(max_retries: int = 5) -> str:
        """Generate a unique reference number with retry on collision."""
        from app import db

        for _ in range(max_retries):
            suffix = secrets.token_hex(4).upper()[:6]
            ref = f"INQ-{suffix}"
            if not db.session.query(db.exists().where(Inquiry.reference_number == ref)).scalar():
                return ref
        raise RuntimeError("Could not generate a unique inquiry reference number")

    @property
    def total_pax(self) -> int:
        """Calculate total number of travelers."""
        return self.num_adults + self.num_children + self.num_infants

    @property
    def is_valid_date_range(self) -> bool:
        """Returns True if travel dates are logically ordered."""
        return self.travel_date_to >= self.travel_date_from

    def __repr__(self) -> str:
        return f"<Inquiry {self.reference_number} - {self.name}>"
