"""Pytest configuration and shared fixtures for test suite."""
import os
import uuid
import pytest
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash


@pytest.fixture()
def app():
    """Create a fresh application and database for every test.

    A brand-new app + database per test (instead of one shared across the
    whole session) means a test can never see data left over by another
    test, and can never inherit a config change another test made.

    Keeping the app context open via `with ... yield ...` for the entire
    test (instead of opening/closing it inside this fixture before handing
    the object back) is what fixes the DetachedInstanceError: the same
    SQLAlchemy session stays alive and bound for as long as the test runs.
    """
    test_db_path = f'test_{uuid.uuid4().hex}.db'

    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key-do-not-use-in-production'
    os.environ['DATABASE_URL'] = f'sqlite:///{test_db_path}'
    os.environ['ADMIN_EMAIL'] = 'admin@test.com'
    os.environ['ADMIN_PASSWORD'] = 'TestPass123'
    os.environ['REQUIRE_EMAIL_VERIFICATION'] = 'false'
    # Force mail off — without this, a real MAIL_USERNAME/PASSWORD sitting in
    # .env gets picked up by load_dotenv() and tests will try to make a real
    # outbound SMTP connection (slow at best, and a real bug to depend on
    # live network/Gmail access just to run the test suite).
    os.environ['MAIL_USERNAME'] = ''
    os.environ['MAIL_PASSWORD'] = ''

    from app import create_app, db

    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db_path}'

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
        # Windows holds an OS-level file lock on the SQLite file for as long
        # as any pooled connection is open, even after drop_all(). Dispose
        # the engine to close every pooled connection before we try to
        # delete the file below — without this, os.remove() raises
        # PermissionError: [WinError 32] on Windows (Linux/Mac don't have
        # this problem, since they allow unlinking a file that's still open).
        db.engine.dispose()

    db_file = os.path.join(flask_app.instance_path, test_db_path)
    for path in (db_file, test_db_path):
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                # Best-effort cleanup — a leftover temp test DB file is
                # harmless and shouldn't fail the test run.
                pass


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner for testing commands."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create test user.

    No nested `with app.app_context()` here on purpose — the `app` fixture
    above already holds one open for the whole test, and opening a second
    one would hand this object a different (and short-lived) SQLAlchemy
    session than the rest of the test runs in.
    """
    from app import db
    from models.user import User

    user = User(
        name='Test User',
        email='testuser@example.com',
        password=generate_password_hash('TestPass123!'),
        phone='+1234567890',
        is_admin=False,
        email_verified=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app):
    """Create admin test user."""
    from app import db
    from models.user import User

    admin = User(
        name='Admin User',
        email='admin@example.com',
        password=generate_password_hash('AdminPass123!'),
        is_admin=True,
        email_verified=True,
    )
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def test_package(app):
    """Create test tour package."""
    from app import db
    from models.package import TourPackage

    package = TourPackage(
        title='Test Package',
        description='A test tour package',
        destination='Test Destination',
        duration_days=7,
        price=5000.00,
        currency='PHP',
        image='default_tour.jpg',
        is_active=True
    )
    db.session.add(package)
    db.session.commit()
    return package


@pytest.fixture
def authenticated_client(client, test_user):
    """Client authenticated as test user.

    Sets Flask-Login's session keys directly rather than calling
    login_user() — login_user() needs a real request context, which
    session_transaction() doesn't reliably provide.
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Client authenticated as admin."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client