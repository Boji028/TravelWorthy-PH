"""HeroSlide model for admin-managed homepage hero background rotation."""
from datetime import datetime, timezone
from app import db


class HeroSlide(db.Model):
    """Each row is one image shown in the homepage hero background rotation.

    Admin-managed via /admin/hero-slides. If no rows exist, the homepage
    falls back to SiteSettings.hero_image plus package cover photos —
    see routes/main.py's home() and templates/main/home.html.
    """

    __tablename__ = "hero_slides"

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<HeroSlide {self.id}>"