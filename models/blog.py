from app import db
from datetime import datetime, timezone


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False, default="Admin")
    category = db.Column(db.String(100), nullable=True, index=True)
    short_description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(300), nullable=True)
    featured_image_size_kb = db.Column(db.Float, nullable=True)  # Track image size
    featured_image_uploaded_at = db.Column(db.DateTime, nullable=True)  # Track upload time
    is_published = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<BlogPost {self.id} - {self.title}>"
