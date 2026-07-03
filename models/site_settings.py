"""Site-wide settings model for admin-configurable homepage backgrounds."""
from datetime import datetime, timezone
from app import db


class SiteSettings(db.Model):
    """Singleton table holding site-wide configurable settings.

    There should only ever be one row in this table. Use
    SiteSettings.get_settings() to fetch it (creating it on first use).
    """

    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)

    hero_image = db.Column(db.String(300), nullable=True)
    hero_image_size_kb = db.Column(db.Float, nullable=True)
    hero_image_uploaded_at = db.Column(db.DateTime, nullable=True)

    testimonial_image = db.Column(db.String(300), nullable=True)
    testimonial_image_size_kb = db.Column(db.Float, nullable=True)
    testimonial_image_uploaded_at = db.Column(db.DateTime, nullable=True)

    cta_image = db.Column(db.String(300), nullable=True)
    cta_image_size_kb = db.Column(db.Float, nullable=True)
    cta_image_uploaded_at = db.Column(db.DateTime, nullable=True)

    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def get_settings(cls):
        """Return the single settings row, creating it on first use."""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self) -> str:
        return "<SiteSettings>"
