from app import db
from datetime import datetime, timezone

class VisaCountry(db.Model):
    __tablename__ = 'visa_countries'

    id = db.Column(db.Integer, primary_key=True)
    country_name = db.Column(db.String(100), nullable=False)
    flag_emoji = db.Column(db.String(10), nullable=True)
    requirements_pdf = db.Column(db.String(300), nullable=True)
    country_image = db.Column(db.String(300), nullable=True)
    country_image_size_kb = db.Column(db.Float, nullable=True)  # Track image size
    country_image_uploaded_at = db.Column(db.DateTime, nullable=True)  # Track upload time
    price = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<VisaCountry {self.country_name}>'