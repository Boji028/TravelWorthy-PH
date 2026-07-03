from app import db
from datetime import datetime, timezone


class Country(db.Model):
    __tablename__ = "countries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    flag_emoji = db.Column(db.String(10), nullable=True)
    image = db.Column(db.String(300), nullable=True)
    image_size_kb = db.Column(db.Float, nullable=True)  # Track image size
    image_uploaded_at = db.Column(db.DateTime, nullable=True)  # Track upload time
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    continent_id = db.Column(db.Integer, db.ForeignKey("continents.id"), nullable=True)
    packages = db.relationship("TourPackage", backref="country", lazy=True)

    def __repr__(self):
        return f"<Country {self.name}>"
