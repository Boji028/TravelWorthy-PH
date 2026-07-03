"""Package image model for multiple photos per tour package."""
from datetime import datetime, timezone
from app import db


class PackageImage(db.Model):
    """Stores multiple images for a single tour package."""

    __tablename__ = "package_images"

    id: int = db.Column(db.Integer, primary_key=True)
    package_id: int = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False, index=True)
    path: str = db.Column(db.String(300), nullable=False)
    order: int = db.Column(db.Integer, default=0)
    uploaded_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<PackageImage {self.id} for package {self.package_id}>"
