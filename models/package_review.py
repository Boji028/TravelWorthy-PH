from datetime import datetime, timezone
from app import db

class PackageReview(db.Model):
    __tablename__ = 'package_reviews'

    id         = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('tour_packages.id', ondelete='CASCADE'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)
    message    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    package = db.relationship('TourPackage', backref='reviews')
    user    = db.relationship('User', backref='package_reviews')

    __table_args__ = (
        db.UniqueConstraint('package_id', 'user_id', name='one_review_per_user_per_package'),
    )