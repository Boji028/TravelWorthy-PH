from app import db
from datetime import datetime, timezone

class Continent(db.Model):
    __tablename__ = 'continents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    flag_emoji = db.Column(db.String(10), nullable=True)
    image = db.Column(db.String(300), nullable=True)
    image_size_kb = db.Column(db.Float, nullable=True)  # Track image size
    image_uploaded_at = db.Column(db.DateTime, nullable=True)  # Track upload time
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    countries = db.relationship('Country', backref='continent', lazy=True)

    def __repr__(self):
        return f'<Continent {self.name}>'