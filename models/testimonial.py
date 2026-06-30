from app import db
from datetime import datetime, timezone

class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    __test__ = False  # tell pytest this is a model, not a test class
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    image = db.Column(db.String(300), nullable=True)
    image_size_kb = db.Column(db.Float, nullable=True)  # Track image size
    image_uploaded_at = db.Column(db.DateTime, nullable=True)  # Track upload time
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('testimonials', passive_deletes=True))

    # BUG-14 fix: one TestimonialImage row per uploaded image instead of comma-separated string
    images = db.relationship(
        'TestimonialImage',
        backref='testimonial',
        lazy=True,
        order_by='TestimonialImage.order',
        cascade='all, delete-orphan'
    )