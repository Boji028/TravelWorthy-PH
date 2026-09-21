from datetime import datetime, timezone
from app import db


class PackageReview(db.Model):
    __tablename__ = "package_reviews"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    # Optional: reviews are entered by admin now (customers have no
    # accounts), so most won't point at a user at all. Older reviews
    # still link to the customer who wrote them.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    # The client's name as admin typed it. The review's own copy, so it
    # survives even if a linked user account is later deleted.
    reviewer_name = db.Column(db.String(100), nullable=True)
    # Optional client photo, shown as the reviewer's avatar.
    image = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    package = db.relationship("TourPackage", backref=db.backref("reviews", cascade="all, delete-orphan"))
    # No delete cascade: deleting a user account used to take all of
    # that customer's reviews with it. Now the link is just cleared and
    # the review stays, keeping its reviewer_name.
    user = db.relationship("User", backref=db.backref("package_reviews"))

    __table_args__ = (db.UniqueConstraint("package_id", "user_id", name="one_review_per_user_per_package"),)

    @property
    def display_name(self) -> str:
        """Name to show publicly - the stored name, else the linked account's."""
        if self.reviewer_name:
            return self.reviewer_name
        if self.user:
            return self.user.name
        return "Guest"
