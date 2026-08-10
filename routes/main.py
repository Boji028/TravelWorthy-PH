"""Main routes for public pages and contact functionality."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload
import bleach
from app import db
from models.testimonial import Testimonial
from models.package import TourPackage
from image_service import ImageUploadService, ImageUploadException
from utils import delete_old_image
from models.blog import BlogPost

main_bp = Blueprint("main", __name__)

ALLOWED_TAGS = ["b", "i", "u", "em", "strong", "p", "br", "ul", "ol", "li"]


@main_bp.route("/")
def home():
    """Home page with featured packages."""
    featured = (
        TourPackage.query.options(selectinload(TourPackage.images))
        .filter_by(is_active=True, is_featured=True)
        .order_by(TourPackage.created_at.desc())
        .limit(6)
        .all()
    )
    packages = (
        featured
        if featured
        else TourPackage.query.options(selectinload(TourPackage.images))
        .filter_by(is_active=True)
        .order_by(TourPackage.created_at.desc())
        .limit(6)
        .all()
    )
    from models.continent import Continent
    from models.site_settings import SiteSettings

    testimonials = (
        Testimonial.query.options(selectinload(Testimonial.user)).order_by(Testimonial.created_at.desc()).limit(5).all()
    )
    posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).limit(3).all()
    continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
    site_settings = SiteSettings.get_settings()
    return render_template(
        "main/home.html",
        packages=packages,
        testimonials=testimonials,
        posts=posts,
        continents=continents,
        site_settings=site_settings,
    )


@main_bp.route("/about")
def about():
    """About page."""
    return render_template("main/about.html")


@main_bp.route("/reviews")
def reviews():
    """Reviews/testimonials page with pagination."""
    page = request.args.get("page", 1, type=int)
    pagination = (
        Testimonial.query.options(selectinload(Testimonial.user), selectinload(Testimonial.images))
        .order_by(Testimonial.created_at.desc())
        .paginate(page=page, per_page=12, error_out=False)
    )
    from sqlalchemy import func

    stats = db.session.query(
        func.avg(Testimonial.rating).label("avg"),
        func.count(Testimonial.id).label("total"),
    ).first()
    avg_rating = round(float(stats.avg), 1) if stats.avg else None
    total_reviews = stats.total or 0

    rating_rows = db.session.query(Testimonial.rating, func.count(Testimonial.id)).group_by(Testimonial.rating).all()
    rating_counts = {r: c for r, c in rating_rows}

    return render_template(
        "main/reviews.html",
        testimonials=pagination.items,
        pagination=pagination,
        avg_rating=avg_rating,
        rating_counts=rating_counts,
        total_reviews=total_reviews,
    )


@main_bp.route("/contact")
def contact():
    """Contact page — displays reach-us details only (phone, email, office, hours)."""
    return render_template("main/contact.html")


@main_bp.route("/testimonial", methods=["POST"])
@login_required
def add_testimonial():
    """Add a testimonial with optional image uploads."""
    message = bleach.clean(request.form.get("message", "").strip(), tags=ALLOWED_TAGS, strip=True)
    try:
        rating = max(1, min(5, int(request.form.get("rating", 5))))
    except (ValueError, TypeError):
        rating = 5

    if not message:
        return jsonify(success=False, error="Message is required."), 400
    if len(message) > 500:
        return jsonify(success=False, error="Review must be 500 characters or fewer."), 400

    existing = Testimonial.query.filter_by(user_id=current_user.id).first()
    if existing:
        return jsonify(success=False, error="You have already submitted a testimonial."), 400

    image_files: list = [f for f in request.files.getlist("image") if f and f.filename]
    image_filenames: list = []
    upload_results: list = []

    if len(image_files) > 5:
        return jsonify(success=False, error="Maximum 5 photos allowed."), 400

    try:
        for image_file in image_files:
            if image_file and image_file.filename:
                try:
                    upload_result = ImageUploadService.upload_and_compress(image_file, "review")
                    image_filenames.append(upload_result["path"])
                    upload_results.append(upload_result)
                except ImageUploadException as e:
                    for orphan in image_filenames:
                        try:
                            delete_old_image(orphan, current_app.config["UPLOAD_FOLDER"])
                        except Exception:
                            pass
                    return jsonify(success=False, error=str(e)), 400

        from models.testimonial_image import TestimonialImage

        testimonial = Testimonial(
            user_id=current_user.id,
            message=message,
            rating=rating,
        )
        db.session.add(testimonial)
        db.session.flush()  # Get testimonial.id before adding images

        # Create one TestimonialImage row per uploaded image
        for i, (url, result) in enumerate(zip(image_filenames, upload_results)):
            img = TestimonialImage(testimonial_id=testimonial.id, path=url, order=i)
            db.session.add(img)

        db.session.commit()

        image_urls = image_filenames

        return jsonify(
            success=True,
            id=testimonial.id,
            message=testimonial.message,
            rating=testimonial.rating,
            user_name=current_user.name,
            created_at=testimonial.created_at.strftime("%B %d, %Y"),
            delete_url=url_for("main.delete_testimonial", testimonial_id=testimonial.id),
            is_admin=current_user.is_admin,
            image_urls=image_urls,
        )

    except Exception as e:
        db.session.rollback()
        for orphan in image_filenames:
            try:
                delete_old_image(orphan, current_app.config["UPLOAD_FOLDER"])
            except Exception as cleanup_err:
                current_app.logger.warning(f"Could not clean up orphaned upload {orphan}: {cleanup_err}")
        current_app.logger.error(f"Testimonial creation failed: {e}", exc_info=True)
        return jsonify(success=False, error="Failed to add testimonial"), 500


@main_bp.route("/testimonial/delete/<int:testimonial_id>", methods=["POST"])
@login_required
def delete_testimonial(testimonial_id):
    if not current_user.is_admin:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, error="Access denied."), 403
        flash("Access denied.", "danger")
        return redirect(url_for("main.home"))

    testimonial = db.get_or_404(Testimonial, testimonial_id)

    from models.testimonial_image import TestimonialImage

    images = TestimonialImage.query.filter_by(testimonial_id=testimonial.id).all()
    image_paths = [img.path for img in images]

    db.session.delete(testimonial)
    db.session.commit()

    for path in image_paths:
        delete_old_image(path, current_app.config["UPLOAD_FOLDER"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True)
    flash("Review deleted.", "success")
    return redirect(url_for("main.reviews"))


@main_bp.route("/inquiry/<reference_number>")
def track_inquiry(reference_number):
    """Public inquiry status tracker — no login required.
    The reference number itself is the access token, same trust model
    as a parcel tracking code (it's a 6-char random hex, unguessable)."""
    from models.inquiry import Inquiry

    inquiry = Inquiry.query.filter_by(reference_number=reference_number.strip().upper()).first()
    if not inquiry:
        return render_template("main/inquiry_status.html", inquiry=None, reference_number=reference_number), 404

    viewing_as_admin = current_user.is_authenticated and current_user.is_admin and inquiry.user_id != current_user.id
    return render_template("main/inquiry_status.html", inquiry=inquiry, viewing_as_admin=viewing_as_admin)


@main_bp.route("/sitemap.xml")
def sitemap():
    """Dynamically generated sitemap including all packages and blog posts."""
    from flask import Response

    pages = []
    # Use configured SITE_URL to prevent Host Header Injection
    # (attacker could send Host: evil.com to inject URLs into the sitemap)
    base = current_app.config.get("SITE_URL", request.host_url).rstrip("/")

    # Static pages
    static_pages = [
        ("/", "1.0"),
        ("/packages", "0.9"),
        ("/packages/visa", "0.8"),
        ("/blog", "0.7"),
        ("/about", "0.6"),
        ("/reviews", "0.6"),
        ("/contact", "0.5"),
    ]
    for path, priority in static_pages:
        pages.append(
            f"""
  <url>
    <loc>{base}{path}</loc>
    <priority>{priority}</priority>
  </url>"""
        )

    # Package pages
    packages = TourPackage.query.filter_by(is_active=True).all()
    for pkg in packages:
        pages.append(
            f"""
  <url>
    <loc>{base}/packages/{pkg.id}</loc>
    <lastmod>{pkg.created_at.strftime('%Y-%m-%d')}</lastmod>
    <priority>0.8</priority>
  </url>"""
        )

    # Blog pages
    posts = BlogPost.query.filter_by(is_published=True).all()
    for post in posts:
        pages.append(
            f"""
  <url>
    <loc>{base}/blog/{post.id}</loc>
    <lastmod>{post.created_at.strftime('%Y-%m-%d')}</lastmod>
    <priority>0.7</priority>
  </url>"""
        )

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    xml += "".join(pages)
    xml += "\n</urlset>"

    return Response(xml, mimetype="application/xml")


@main_bp.route("/my-inquiries")
@login_required
def my_inquiries():
    """List every inquiry the logged-in user has submitted."""
    from models.inquiry import Inquiry

    inquiries = Inquiry.query.filter_by(user_id=current_user.id).order_by(Inquiry.created_at.desc()).all()
    return render_template("main/my_inquiries.html", inquiries=inquiries)


@main_bp.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    """Mark all of the current user's notifications as read.
    Called via fetch() when the bell dropdown is opened."""
    from models.inquiry_notification import InquiryNotification

    InquiryNotification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify(success=True)


@main_bp.route("/notifications/<int:notification_id>/mark-read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    """Mark a single notification as read. Called via fetch right before
    the browser navigates to that notification's destination link."""
    from models.inquiry_notification import InquiryNotification

    notif = InquiryNotification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    if notif and not notif.is_read:
        notif.is_read = True
        db.session.commit()
    return jsonify(success=True)
