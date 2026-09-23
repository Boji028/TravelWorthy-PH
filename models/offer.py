from app import db
from datetime import datetime, timezone
from models.travel_date import format_date_range

# Fixed list so the public filter pills stay tidy; edit here to add a category.
OFFER_CATEGORIES = ["Corporate Incentive", "Team Building", "Field Trip", "Events", "Other"]


class Offer(db.Model):
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="Other")
    summary = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)
    flier_image = db.Column(db.String(300), nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=True)
    min_pax = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    highlights = db.Column(db.Text, nullable=True)
    inclusions = db.Column(db.Text, nullable=True)
    exclusions = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    images = db.relationship(
        "OfferImage", backref="offer", lazy=True, order_by="OfferImage.order", cascade="all, delete-orphan"
    )
    dates = db.relationship("OfferDate", backref="offer", lazy=True, order_by="OfferDate.date", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Offer {self.title}>"


class OfferImage(db.Model):
    """One gallery photo for an offer."""

    __tablename__ = "offer_images"

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    path = db.Column(db.String(300), nullable=False)
    order = db.Column(db.Integer, default=0)


class OfferDate(db.Model):
    """One available date or date range for an offer, with an optional note."""

    __tablename__ = "offer_dates"

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    note = db.Column(db.String(100), nullable=True)

    @property
    def display_range(self) -> str:
        return format_date_range(self.date, self.end_date)

    @property
    def as_form(self) -> dict:
        """Values for pre-filling the admin date rows."""
        return {"date": self.date.isoformat(), "end_date": self.end_date.isoformat() if self.end_date else "", "note": self.note or ""}
