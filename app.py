import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per day", "60 per hour", "10 per minute"],
)
mail = Mail()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Render (and most PaaS platforms) terminate HTTPS at a reverse proxy
    # in front of the container - the app itself only ever sees plain
    # HTTP internally, even though the visitor is on https://. Without
    # this, url_for(_external=True) (used for the Google OAuth redirect
    # URI, password reset links, and email verification links) can build
    # an http:// URL, which Google rejects with redirect_uri_mismatch
    # even when the console's configured redirect URI is correct.
    # x_for/x_proto=1: trust exactly one proxy hop, matching Render's
    # architecture (client -> Render's edge proxy -> this container).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ── Config ────────────────────────────────────────────────
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY is not set in your .env file!")
    app.config["SECRET_KEY"] = secret
    # Belt-and-suspenders for any external URL built outside a request
    # context (none currently exist, but cheap to set): without a
    # request to read the scheme from, Flask falls back to this.
    if os.getenv("FLASK_FORCE_HTTPS", "false").lower() == "true":
        app.config["PREFERRED_URL_SCHEME"] = "https"

    # Database
    database_url = os.getenv("DATABASE_URL", "sqlite:///travel_agency.db")
    if database_url and "postgresql://" in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if "postgresql" in database_url:
        # Recycle connections before the server's idle timeout kills them.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 280, "pool_pre_ping": True}

    db_type = "PostgreSQL" if "postgresql" in database_url else "SQLite"
    app.logger.info(f"Using {db_type} database")

    # Uploads
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.config["MAX_CONTENT_LENGTH"] = 27 * 1024 * 1024  # 27 MB

    # Flask-Mail
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME", ""))

    # Site URL for email links
    site_url = os.getenv("SITE_URL")
    if site_url:
        app.config["SITE_URL"] = site_url

    # Email verification
    _verification_default = "true" if os.getenv("FLASK_ENV") == "production" else "false"
    app.config["REQUIRE_EMAIL_VERIFICATION"] = os.getenv("REQUIRE_EMAIL_VERIFICATION", _verification_default).lower() == "true"

    if app.config["REQUIRE_EMAIL_VERIFICATION"]:
        app.logger.info("Email verification is required before login")
        if not app.config.get("MAIL_USERNAME"):
            app.logger.warning(
                "REQUIRE_EMAIL_VERIFICATION is enabled but MAIL_USERNAME is not set — " "verification emails cannot be sent"
            )
    else:
        app.logger.info("Email verification is disabled (users can log in immediately after registration)")

    # Debug
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Session Security
    from datetime import timedelta

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
    # Use explicit FLASK_SECURE_COOKIES env var; FLASK_ENV is deprecated in Flask 3.x.
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_SECURE_COOKIES", "false").lower() == "true"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True

    # ── Init extensions ────────────────────────────────────────
    db.init_app(app)

    # CSP — 'unsafe-inline' in script-src works because no nonce is generated
    csp = {
        "default-src": "'self'",
        "script-src": ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com"],
        "style-src": ["'self'", "'unsafe-inline'", "fonts.googleapis.com", "cdnjs.cloudflare.com"],
        "font-src": ["'self'", "fonts.gstatic.com", "cdnjs.cloudflare.com"],
        "img-src": ["'self'", "data:", "blob:", "res.cloudinary.com", "flagcdn.com"],
        "connect-src": ["'self'", "https://api.cloudinary.com"],
        "frame-src": ["'self'", "https://www.google.com", "https://maps.google.com", "https://res.cloudinary.com"],
    }
    force_https = os.getenv("FLASK_FORCE_HTTPS", "false").lower() == "true"
    Talisman(app, content_security_policy=csp, force_https=force_https)
    # csp_nonce() is still called in templates — return empty string so they don't crash
    app.jinja_env.globals["csp_nonce"] = lambda: ""

    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    from oauth import init_oauth

    init_oauth(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # ── Serve uploads ──────────────────────────────────────────
    # FIX 6: Use pathlib for safe path resolution
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        from flask import send_from_directory, abort
        from pathlib import Path

        ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf"}

        upload_root = Path(app.config["UPLOAD_FOLDER"]).resolve()
        requested = (upload_root / filename).resolve()

        if not requested.is_relative_to(upload_root):
            abort(403)

        ext = requested.suffix.lstrip(".").lower()
        if ext not in ALLOWED_EXTENSIONS:
            abort(404)

        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ── SEO files ──────────────────────────────────────────────
    @app.route("/robots.txt")
    def robots():
        return app.send_static_file("robots.txt")

    # ── Register blueprints ────────────────────────────────────
    from routes.auth import auth_bp
    from routes.packages import packages_bp
    from routes.bookings import bookings_bp
    from routes.admin import admin_bp
    from routes.main import main_bp
    from routes.blog import blog_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(packages_bp, url_prefix="/packages")
    app.register_blueprint(bookings_bp, url_prefix="/bookings")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(blog_bp, url_prefix="/blog")

    # Admin routes already require login + is_admin (@admin_required on every
    # view in routes/admin.py) — the global rate limits below exist to slow
    # down anonymous/public abuse, not normal staff work. Without this,
    # routine admin use (clicking filter pills, editing several packages in
    # a row) can quietly trip the "10 per minute" default and return a bare
    # 429 page instead of the expected response — which looks exactly like a
    # button "doing nothing."
    limiter.exempt(admin_bp)
    # ── Register models with SQLAlchemy (imports only — no create_all) ─────────
    with app.app_context():
        from models.user import User
        from models.package import TourPackage
        from models.inquiry import Inquiry
        from models.blog import BlogPost
        from models.continent import Continent
        from models.country import Country
        from models.testimonial import Testimonial
        from models.testimonial_image import TestimonialImage
        from models.visa import VisaCountry
        from models.package_image import PackageImage
        from models.package_review import PackageReview
        from models.inquiry_notification import InquiryNotification
        from models.wishlist import WishlistItem

        # Only auto-create tables for ephemeral SQLite databases (quick local
        # experiments, pytest fixtures). Never auto-create against PostgreSQL —
        # even in dev — since that's exactly what silently raced against
        # Alembic and broke a real migration. Postgres always goes through
        # `flask db upgrade`, regardless of FLASK_ENV.
        if "sqlite" in database_url:
            db.create_all()

    # ── Error handlers ─────────────────────────────────────────
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 Internal Server Error: {e}", exc_info=True)
        return render_template("500.html"), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return render_template("429.html"), 429

    # ── File-based logging ─────────────────────────────────────
    try:
        from file_logging import setup_file_logging

        setup_file_logging(app)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")

    from cli import register_commands

    register_commands(app)

    # ── Cloudinary auto-enhance filter for templates ──────────────────
    @app.template_filter("cloudinary_card")
    def cloudinary_card(url):
        """Smart-crop, auto-enhance and optimise any Cloudinary image for cards."""
        if not url or not url.startswith("https://res.cloudinary.com"):
            return url
        transforms = (
            "f_auto,"  # serve WebP/AVIF automatically
            "q_auto:best,"  # auto quality — prioritise sharpness
            "w_640,"  # cap width at 640px (2× for retina)
            "ar_4:3,"  # force 4:3 crop
            "c_fill,"  # fill the frame (no empty space)
            "g_center,"  # always crop from centre — consistent across all images
            "e_improve,"  # auto brightness, contrast, colour
            "e_sharpen:40"  # slight sharpening for clarity
        )
        return url.replace("/upload/", f"/upload/{transforms}/")
    @app.template_filter("cloudinary_package_card")
    def cloudinary_package_card(url):
        """Same as cloudinary_card but 16:9 - for package list cards specifically,
        since package images are cropped from 16:9 fliers with a logo/title that
        4:3 center-cropping was clipping. Deliberately separate from
        cloudinary_card so continent tiles, blog images, and other callers of
        that filter are unaffected."""
        if not url or not url.startswith("https://res.cloudinary.com"):
            return url
        transforms = (
            "f_auto,"
            "q_auto:best,"
            "w_640,"
            "ar_16:9,"
            "c_fill,"
            "g_center,"
            "e_improve,"
            "e_sharpen:40"
        )
        return url.replace("/upload/", f"/upload/{transforms}/")

    @app.template_filter("cloudinary_enhance")
    def cloudinary_enhance(url):
        """Enhance Cloudinary image without cropping — for full-size display."""
        if not url or not url.startswith("https://res.cloudinary.com"):
            return url
        transforms = "f_auto,q_auto:best,e_improve,e_sharpen:40"
        return url.replace("/upload/", f"/upload/{transforms}/")

    @app.template_filter("flag_to_iso")
    def flag_to_iso(emoji):
        """Convert a flag value to its 2-letter ISO code (e.g. 'jp').

        Handles two cases:
        1. A plain 2-letter country code already stored as text (e.g. 'JP').
        2. An actual flag emoji built from two Unicode 'Regional Indicator
           Symbol' characters (e.g. 🇯🇵), which encode the same ISO code.
        """
        if not emoji:
            return None
        chars = list(emoji)
        if len(chars) != 2:
            return None
        # Case 1: already plain ASCII letters (e.g. stored as "JP")
        if all(c.isalpha() and c.isascii() for c in chars):
            return "".join(chars).lower()
        # Case 2: actual regional-indicator flag emoji
        try:
            code = "".join(chr(ord(c) - 0x1F1E6 + 65) for c in chars)
            return code.lower() if code.isalpha() and len(code) == 2 else None
        except (ValueError, TypeError):
            return None

    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        if current_user.is_authenticated:

            # Fetch one extra to detect "9+" without a second COUNT query.
            recent_all = (
                InquiryNotification.query.filter_by(user_id=current_user.id, is_read=False)
                .order_by(InquiryNotification.created_at.desc())
                .limit(9)
                .all()
            )
            unread_count = len(recent_all)
            recent = recent_all[:8]
            return {"unread_notification_count": unread_count, "recent_notifications": recent}
        return {"unread_notification_count": 0, "recent_notifications": []}

    @app.template_filter("safe_html")
    def safe_html_filter(content):
        """Sanitize HTML with allowed tags — use instead of | safe for user/admin content."""
        import bleach
        from markupsafe import Markup

        ALLOWED = ["b", "i", "u", "em", "strong", "p", "br", "ul", "ol", "li", "h2", "h3", "a", "blockquote"]
        ATTRS = {"a": ["href", "title"]}
        return Markup(bleach.clean(content or "", tags=ALLOWED, attributes=ATTRS, strip=True))

    return app
