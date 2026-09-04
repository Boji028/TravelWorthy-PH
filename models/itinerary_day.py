"""Itinerary day model for structured day-by-day tour itineraries."""
from app import db


class ItineraryDay(db.Model):
    """A single day within a tour package's itinerary.

    Its own table rather than packed into TourPackage.itinerary (a single
    Text column), matching the PackageImage pattern already used for
    gallery photos — each day gets its own row with a title, a meals
    line, and a description, instead of one big freeform blob.
    """

    __tablename__ = "itinerary_days"

    id: int = db.Column(db.Integer, primary_key=True)
    package_id: int = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False, index=True)
    day_number: int = db.Column(db.Integer, nullable=False)
    title: str = db.Column(db.String(200), nullable=False)
    meals: str = db.Column(db.String(50), nullable=True)
    description: str = db.Column(db.Text, nullable=True)
    # Optional Cloudinary URL for a photo of this day, shown as a thumbnail
    # on the public itinerary. Nullable because most existing days have no
    # image and the itinerary has to render fine without one.
    image: str = db.Column(db.String(500), nullable=True)
    order: int = db.Column(db.Integer, default=0)

    def __repr__(self) -> str:
        return f"<ItineraryDay {self.day_number} for package {self.package_id}>"