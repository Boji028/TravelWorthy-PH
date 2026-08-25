"""Travel date model for admin-managed departure dates on a tour package."""
from datetime import date as _date
from app import db


class TravelDate(db.Model):
    """A single scheduled departure date (optionally a range) for a tour package.

    Its own table rather than packed into TourPackage, matching the
    ItineraryDay/PackageImage pattern already used for other per-package
    lists — each date gets its own row with an optional short note (e.g.
    "Early Bird", "Peak Season") instead of one freeform text field.

    end_date is optional: leave it blank for a single-day departure, or
    set it for a multi-day range (e.g. Dec 21-25). display_range below
    formats either case for the public page.
    """

    __tablename__ = "travel_dates"

    id: int = db.Column(db.Integer, primary_key=True)
    package_id: int = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    note: str = db.Column(db.String(100), nullable=True)

    @property
    def display_range(self) -> str:
        """Human-readable date or date range for the public page.

        Examples: "December 21, 2026" (no end date), "December 21 - 25,
        2026" (same month), "December 28 - January 2, 2027" (crosses a
        month), "December 28, 2026 - January 2, 2027" (crosses a year).
        """
        if not self.end_date or self.end_date == self.date:
            return self.date.strftime("%B %d, %Y")
        if self.end_date.year != self.date.year:
            return f"{self.date.strftime('%B %d, %Y')} - {self.end_date.strftime('%B %d, %Y')}"
        if self.end_date.month != self.date.month:
            return f"{self.date.strftime('%B %d')} - {self.end_date.strftime('%B %d, %Y')}"
        return f"{self.date.strftime('%B %d')} - {self.end_date.strftime('%d, %Y')}"

    @property
    def weeks_away(self) -> int:
        """Roughly how many full weeks from today until this date starts.

        Used for the "in X wks" label on the public dates list, which
        matters more than the month name alone once a package has
        departures spread across several months. Clamps to 0 instead of
        going negative for a past date — callers that only want future
        departures should filter those out first (see package_detail()
        in routes/packages.py), this is just a display safeguard.
        """
        days = (self.date - _date.today()).days
        return max(round(days / 7), 0)

    def __repr__(self) -> str:
        return f"<TravelDate {self.date} for package {self.package_id}>"