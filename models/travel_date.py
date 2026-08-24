"""Travel date model for admin-managed departure dates on a tour package."""
from app import db


class TravelDate(db.Model):
    """A single scheduled departure date for a tour package.

    Its own table rather than packed into TourPackage, matching the
    ItineraryDay/PackageImage pattern already used for other per-package
    lists — each date gets its own row with an optional short note (e.g.
    "Early Bird", "Peak Season") instead of one freeform text field.
    """

    __tablename__ = "travel_dates"

    id: int = db.Column(db.Integer, primary_key=True)
    package_id: int = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    note: str = db.Column(db.String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<TravelDate {self.date} for package {self.package_id}>"