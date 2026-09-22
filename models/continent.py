from app import db
from datetime import datetime, timezone


# Curated display order for the public-facing continent filter (packages
# page toolbar) and the homepage "Browse by Region" section. Asia leads
# since Travel Worthy PH is a Philippines-based agency and most packages
# are Asian destinations. This is a plain list, not a database column, so
# reordering it later just means editing the names below and redeploying.
# Any continent added in admin that isn't in this list still shows up -
# it's appended alphabetically after the ones below, so it never silently
# disappears from the filter bar.
CONTINENT_DISPLAY_ORDER = [
    "Asia",
    "Europe",
    "North America",
    "Oceania",
    "Africa",
    "South America",
    "Antarctica",
]


class Continent(db.Model):
    __tablename__ = "continents"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    flag_emoji = db.Column(db.String(10), nullable=True)
    image = db.Column(db.String(300), nullable=True)
    image_size_kb = db.Column(db.Float, nullable=True)  # Track image size
    image_uploaded_at = db.Column(db.DateTime, nullable=True)  # Track upload time
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    countries = db.relationship("Country", backref="continent", lazy=True)

    def __repr__(self):
        return f"<Continent {self.name}>"

    @classmethod
    def ordered_active(cls):
        """Active continents in the curated CONTINENT_DISPLAY_ORDER.

        Used for the public filter/browse UI. Continents not listed in
        CONTINENT_DISPLAY_ORDER are appended afterward, alphabetically,
        so a newly-added continent still appears even before someone
        remembers to add it to the list above.
        """
        continents = cls.query.filter_by(is_active=True).all()

        def sort_key(continent):
            try:
                position = CONTINENT_DISPLAY_ORDER.index(continent.name)
            except ValueError:
                position = len(CONTINENT_DISPLAY_ORDER)
            return (position, continent.name)

        continents.sort(key=sort_key)
        return continents