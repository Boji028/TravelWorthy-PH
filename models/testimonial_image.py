"""TestimonialImage model for storing multiple images per testimonial."""
from datetime import datetime, timezone
from app import db


class TestimonialImage(db.Model):
    """Each row is one image belonging to a testimonial."""

    __tablename__ = "testimonial_images"
    __test__ = False  # tell pytest this is a model, not a test class

    id = db.Column(db.Integer, primary_key=True)
    testimonial_id = db.Column(db.Integer, db.ForeignKey("testimonials.id", ondelete="CASCADE"), nullable=False, index=True)
    path = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TestimonialImage {self.id} for testimonial {self.testimonial_id}>"
