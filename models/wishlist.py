"""Wishlist model for saved packages and visa countries."""
from typing import Optional
from datetime import datetime, timezone
from app import db


class WishlistItem(db.Model):
    """A tour package or visa country a user has saved for later.

    Exactly one of package_id/visa_id is set per row (enforced by
    ck_wishlist_exactly_one_target) - a single table with a CheckConstraint
    rather than two separate join tables, matching the CheckConstraint idiom
    already used on Inquiry. Because that constraint requires exactly one FK
    to be non-null, cascade='all, delete-orphan' is required on all three
    parent sides (not just User) - otherwise deleting a TourPackage or
    VisaCountry would null out its FK here and leave a row with both FKs
    null, violating the constraint instead of just leaving an orphan.
    """

    __tablename__ = "wishlist_items"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=True, index=True)
    visa_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("visa_countries.id"), nullable=True, index=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "package_id", name="uq_wishlist_user_package"),
        db.UniqueConstraint("user_id", "visa_id", name="uq_wishlist_user_visa"),
        db.CheckConstraint(
            "(package_id IS NOT NULL AND visa_id IS NULL) OR (package_id IS NULL AND visa_id IS NOT NULL)",
            name="ck_wishlist_exactly_one_target",
        ),
    )

    user = db.relationship("User", backref=db.backref("wishlist_items", cascade="all, delete-orphan"))
    package = db.relationship("TourPackage", backref=db.backref("wishlist_items", cascade="all, delete-orphan"))
    visa = db.relationship("VisaCountry", backref=db.backref("wishlist_items", cascade="all, delete-orphan"))

    @staticmethod
    def saved_ids(user_id: int, column) -> set:
        """Return the set of package_id (or visa_id) values a user has
        saved, for cheaply marking hearts as filled in a card grid."""
        rows = WishlistItem.query.filter_by(user_id=user_id).filter(column.isnot(None)).with_entities(column).all()
        return {row[0] for row in rows}

    def __repr__(self) -> str:
        target = f"package={self.package_id}" if self.package_id else f"visa={self.visa_id}"
        return f"<WishlistItem user={self.user_id} {target}>"
