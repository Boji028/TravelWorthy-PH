import os
import traceback
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db            = SQLAlchemy()
login_manager = LoginManager()
csrf          = CSRFProtect()
limiter       = Limiter(key_func=get_remote_address, default_limits=[])
mail          = Mail()
migrate       = Migrate()


def create_app():
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────
    secret = os.getenv('SECRET_KEY')
    if not secret:
        raise RuntimeError("SECRET_KEY is not set in your .env file!")
    app.config['SECRET_KEY'] = secret

    # Database
    database_url = os.getenv('DATABASE_URL', 'sqlite:///travel_agency.db')
    if database_url and 'postgresql://' in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db_type = 'PostgreSQL' if 'postgresql' in database_url else 'SQLite'
    app.logger.info(f'Using {db_type} database')

    # Uploads — separate from static assets
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # FIX: align MAX_CONTENT_LENGTH with ImageUploadService.MAX_IMAGE_SIZE_MB (25 MB)
    # Adding a small buffer (2 MB) for multipart form overhead so Flask doesn't reject
    # a valid 25 MB upload before the service-level check even runs.
    app.config['MAX_CONTENT_LENGTH'] = 27 * 1024 * 1024  # 27 MB

    # Flask-Mail
    app.config['MAIL_SERVER']         = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT']           = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS']        = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME']       = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD']       = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME', ''))

    # Site URL for email links
    app.config['SITE_URL'] = os.getenv('SITE_URL', 'http://localhost:5000')

    # Debug — never hardcode True
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # Session Security Configuration
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV', 'development') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

    # ── Init extensions ────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # ── Serve uploads ──────────────────────────────────────────
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ── Register blueprints ────────────────────────────────────
    from routes.auth import auth_bp
    from routes.packages import packages_bp
    from routes.bookings import bookings_bp
    from routes.admin import admin_bp
    from routes.main import main_bp
    from routes.blog import blog_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(packages_bp, url_prefix='/packages')
    app.register_blueprint(bookings_bp, url_prefix='/bookings')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(blog_bp, url_prefix='/blog')

    # ── Create tables & default admin ─────────────────────────
    with app.app_context():
        from models.user import User
        from models.package import TourPackage
        from models.inquiry import Inquiry
        from models.blog import BlogPost
        from models.continent import Continent
        from models.country import Country
        from models.testimonial import Testimonial
        from models.visa import VisaCountry
        from models.contact import ContactMessage
        from models.booking import Booking
        db.create_all()

        admin_email    = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        if not admin_email or not admin_password:
            raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env!")
        
        # FIX: Wrap admin creation in try-except to handle incomplete schema during migrations
        try:
            from werkzeug.security import generate_password_hash
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    name='Admin',
                    email=admin_email,
                    password=generate_password_hash(admin_password),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Default admin created!")
        except Exception as e:
            # Database schema may be incomplete - migrations need to run
            # This is safe - migrations will handle admin creation
            app.logger.debug(f"Skipping admin creation during app init (likely migration needed): {e}")


    # ── Error handlers ─────────────────────────────────────────
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        traceback.print_exc()
        print(f"500 ERROR: {e}", flush=True)
        return render_template('500.html'), 500

    # ── File-based logging ─────────────────────────────────────
    try:
        from file_logging import setup_file_logging
        setup_file_logging(app)
    except Exception as e:
        print(f'Warning: Could not setup file logging: {e}')

    return app
