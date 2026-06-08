"""Tests for data models."""
import pytest
from datetime import datetime, timezone
from models.user import User
from models.package import TourPackage
from models.booking import Booking
from werkzeug.security import check_password_hash, generate_password_hash


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, app):
        """Test creating a user."""
        with app.app_context():
            from app import db
            user = User(
                name='Test User',
                email='test@example.com',
                password=generate_password_hash('TestPass123'),
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == 'test@example.com'
            assert check_password_hash(user.password, 'TestPass123')

    def test_user_repr(self, test_user):
        """Test user string representation."""
        assert 'test' in repr(test_user).lower()

    def test_user_admin_flag(self, app):
        """Test admin flag on user."""
        with app.app_context():
            from app import db
            user = User(
                name='Admin User',
                email='admin@example.com',
                password=generate_password_hash('AdminPass123'),
                is_admin=True
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.is_admin is True

    def test_user_timestamps(self, test_user):
        """Test that user has creation timestamp."""
        assert test_user.created_at is not None
        assert isinstance(test_user.created_at, datetime)


class TestTourPackageModel:
    """Test TourPackage model."""

    def test_package_creation(self, app):
        """Test creating a tour package."""
        with app.app_context():
            from app import db
            package = TourPackage(
                title='Test Tour',
                description='A test tour',
                destination='Test Destination',
                duration_days=7,
                price=5000.00,
                currency='PHP',
                max_slots=20,
                available_slots=20,
                is_active=True
            )
            db.session.add(package)
            db.session.commit()
            
            assert package.id is not None
            assert package.title == 'Test Tour'
            assert package.available_slots == 20

    def test_package_inactive(self, app):
        """Test inactive package."""
        with app.app_context():
            from app import db
            package = TourPackage(
                title='Inactive Tour',
                description='An inactive tour',
                destination='Test',
                duration_days=3,
                price=1000.00,
                currency='PHP',
                max_slots=10,
                is_active=False
            )
            db.session.add(package)
            db.session.commit()
            
            assert package.is_active is False

    def test_package_currency(self, test_package):
        """Test package currency field."""
        assert test_package.currency == 'PHP'

    def test_package_slots_management(self, app, test_package):
        """Test package slot management."""
        with app.app_context():
            from app import db
            test_package.available_slots = test_package.available_slots - 5
            db.session.commit()
            
            refreshed = TourPackage.query.get(test_package.id)
            assert refreshed.available_slots == 15


class TestBookingModel:
    """Test Booking model."""

    def test_booking_creation(self, app, test_user, test_package):
        """Test creating a booking."""
        with app.app_context():
            from app import db
            from datetime import date
            
            booking = Booking(
                user_id=test_user.id,
                package_id=test_package.id,
                num_travelers=3,
                travel_date=date.today(),
                total_price=15000.00,
                status='pending'
            )
            db.session.add(booking)
            db.session.commit()
            
            assert booking.id is not None
            assert booking.num_travelers == 3

    def test_booking_status(self, test_booking):
        """Test booking status."""
        assert test_booking.status == 'pending'

    def test_booking_total_price(self, test_booking):
        """Test booking total price."""
        assert test_booking.total_price == 10000.00

    def test_booking_timestamps(self, test_booking):
        """Test booking timestamps."""
        assert test_booking.created_at is not None
        assert isinstance(test_booking.created_at, datetime)

    def test_booking_relationships(self, app, test_booking, test_user, test_package):
        """Test booking relationships."""
        with app.app_context():
            # Refresh from database
            booking = Booking.query.get(test_booking.id)
            
            assert booking.user.email == test_user.email
            assert booking.package.title == test_package.title

    def test_booking_repr(self, test_booking):
        """Test booking string representation."""
        repr_str = repr(test_booking)
        assert 'pending' in repr_str.lower()


class TestModelConstraints:
    """Test model constraints and validations."""

    def test_unique_email_constraint(self, app, test_user):
        """Test that email must be unique."""
        with app.app_context():
            from app import db
            from sqlalchemy.exc import IntegrityError
            
            duplicate_user = User(
                name='Duplicate',
                email=test_user.email,
                password=generate_password_hash('Password123'),
                is_admin=False
            )
            db.session.add(duplicate_user)
            
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_package_price_positive(self, app):
        """Test that package price can be zero or positive."""
        with app.app_context():
            from app import db
            
            package = TourPackage(
                title='Free Tour',
                description='A free tour',
                destination='Free',
                duration_days=1,
                price=0.00,
                currency='PHP',
                max_slots=100
            )
            db.session.add(package)
            db.session.commit()
            
            assert package.price == 0.00

    def test_booking_relationships_required(self, app):
        """Test that booking requires user and package."""
        with app.app_context():
            from app import db
            from datetime import date
            from sqlalchemy.exc import IntegrityError
            
            # Try to create booking without user_id
            booking = Booking(
                user_id=None,
                package_id=1,
                num_travelers=1,
                travel_date=date.today(),
                total_price=1000.00
            )
            db.session.add(booking)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
