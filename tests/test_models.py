"""Tests for data models."""
import pytest
from datetime import datetime, timezone
from models.user import User
from models.package import TourPackage
from models.agent import Agent
from werkzeug.security import check_password_hash, generate_password_hash


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, app):
        """Test creating a user."""
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
        from app import db
        package = TourPackage(
            title='Test Tour',
            description='A test tour',
            destination='Test Destination',
            duration_days=7,
            price=5000.00,
            currency='PHP',
            is_active=True
        )
        db.session.add(package)
        db.session.commit()

        assert package.id is not None
        assert package.title == 'Test Tour'

    def test_package_inactive(self, app):
        """Test inactive package."""
        from app import db
        package = TourPackage(
            title='Inactive Tour',
            description='An inactive tour',
            destination='Test',
            duration_days=3,
            price=1000.00,
            currency='PHP',
            is_active=False
        )
        db.session.add(package)
        db.session.commit()

        assert package.is_active is False

    def test_package_currency(self, test_package):
        """Test package currency field."""
        assert test_package.currency == 'PHP'


class TestAgentModel:
    """Test Agent model."""

    def test_agent_creation_defaults(self, app):
        """Test creating an agent relies on the right column defaults."""
        from app import db
        agent = Agent(name='Juan Dela Cruz', email='juan@travelworthyph.com')
        db.session.add(agent)
        db.session.commit()

        assert agent.id is not None
        assert agent.is_active is True
        assert agent.is_visa_agent is False
        assert agent.created_at is not None

    def test_agent_repr(self, app):
        """Test agent string representation."""
        from app import db
        agent = Agent(name='Juan Dela Cruz', email='juan@travelworthyph.com')
        db.session.add(agent)
        db.session.commit()

        assert 'Juan Dela Cruz' in repr(agent)

    def test_package_assigned_agent_relationship(self, app):
        """Test TourPackage.assigned_agent resolves via the relationship,
        not just the raw assigned_agent_id foreign key."""
        from app import db
        agent = Agent(name='Juan Dela Cruz', email='juan@travelworthyph.com')
        db.session.add(agent)
        db.session.commit()

        package = TourPackage(
            title='Test Tour',
            description='A test tour',
            destination='Test Destination',
            duration_days=7,
            price=5000.00,
            currency='PHP',
            assigned_agent_id=agent.id,
        )
        db.session.add(package)
        db.session.commit()

        assert package.assigned_agent.name == 'Juan Dela Cruz'
        assert package in agent.packages


class TestModelConstraints:
    """Test model constraints and validations."""

    def test_unique_email_constraint(self, app, test_user):
        """Test that email must be unique."""
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
        from app import db

        package = TourPackage(
            title='Free Tour',
            description='A free tour',
            destination='Free',
            duration_days=1,
            price=0.00,
            currency='PHP'
        )
        db.session.add(package)
        db.session.commit()

        assert package.price == 0.00