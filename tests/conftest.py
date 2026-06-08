"""Pytest configuration and shared fixtures for test suite."""
import os
import pytest
from datetime import datetime, timezone
from app import create_app, db
from models.user import User
from models.package import TourPackage
from models.booking import Booking
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    """Create application for the test session."""
    # Use test database
    test_db_path = 'travel_agency_test.db'
    
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key-do-not-use-in-production'
    os.environ['DATABASE_URL'] = f'sqlite:///{test_db_path}'
    os.environ['ADMIN_EMAIL'] = 'admin@test.com'
    os.environ['ADMIN_PASSWORD'] = 'TestPass123'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db_path}'
    
    # Create tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Clean up test database file
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


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
    """Create test user."""
    with app.app_context():
        user = User(
            name='Test User',
            email='testuser@example.com',
            password=generate_password_hash('TestPass123!'),
            phone='+1234567890',
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Create admin test user."""
    with app.app_context():
        admin = User(
            name='Admin User',
            email='admin@example.com',
            password=generate_password_hash('AdminPass123!'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def test_package(app):
    """Create test tour package."""
    with app.app_context():
        package = TourPackage(
            title='Test Package',
            description='A test tour package',
            destination='Test Destination',
            duration_days=7,
            price=5000.00,
            currency='PHP',
            max_slots=20,
            available_slots=20,
            image='default_tour.jpg',
            is_active=True
        )
        db.session.add(package)
        db.session.commit()
        return package


@pytest.fixture
def test_booking(app, test_user, test_package):
    """Create test booking."""
    with app.app_context():
        booking = Booking(
            user_id=test_user.id,
            package_id=test_package.id,
            num_travelers=2,
            travel_date=datetime.now(timezone.utc).date(),
            total_price=10000.00,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        return booking


@pytest.fixture
def authenticated_client(client, test_user, app):
    """Client authenticated as test user."""
    with app.app_context():
        with client.session_transaction() as sess:
            from flask_login import login_user
            login_user(test_user)
    return client


@pytest.fixture
def admin_client(client, admin_user, app):
    """Client authenticated as admin."""
    with app.app_context():
        with client.session_transaction() as sess:
            from flask_login import login_user
            login_user(admin_user)
    return client
