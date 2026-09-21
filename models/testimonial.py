from app import db
from datetime import datetime, timezone


class Testimonial(db.Model):
    __tablename__ = "testimonials"
    __test__ = False  # tell pytest this is a model, not a test class
    id = db.Column(db.Integer, primary_key=True)
    # Optional - admin enters testimonials now. See PackageReview.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    reviewer_name = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    image = db.Column(db.String(300), nullable=True)
    image_size_kb = db.Column(db.Float, nullable=True)  # Track image size
    image_uploaded_at = db.Column(db.DateTime, nullable=True)  # Track upload time
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # passive_deletes used to leave this to the database's ON DELETE
    # CASCADE, which deleted testimonials along with their user. Letting
    # the ORM handle it clears user_id instead, so the testimonial stays.
    user = db.relationship("User", backref=db.backref("testimonials"))

    # BUG-14 fix: one TestimonialImage row per uploaded image instead of comma-separated string
    images = db.relationship(
        "TestimonialImage", backref="testimonial", lazy=True, order_by="TestimonialImage.order", cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        """Name to show publicly - the stored name, else the linked account's."""
        if self.reviewer_name:
            return self.reviewer_name
        if self.user:
            return self.user.name
        return "Guest"
