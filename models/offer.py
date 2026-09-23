from app import db
from datetime import datetime, timezone

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
    price = db.Column(db.Numeric(12, 2), nullable=True)
    min_pax = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Offer {self.title}>"
