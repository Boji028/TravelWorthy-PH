"""Tests for data models."""
import pytest
from datetime import datetime, timezone
from models.user import User
from models.package import TourPackage
from models.agent import Agent
from models.visa import VisaCountry
from models.wishlist import WishlistItem
from werkzeug.security import check_password_hash, generate_password_hash


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, app):
        """Test creating a user."""
        from app import db

        user = User(name="Test User", email="test@example.com", password=generate_password_hash("TestPass123"), is_admin=False)
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert check_password_hash(user.password, "TestPass123")

    def test_user_repr(self, test_user):
        """Test user string representation."""
        assert "test" in repr(test_user).lower()

    def test_user_admin_flag(self, app):
        """Test admin flag on user."""
        from app import db

        user = User(
            name="Admin User", email="admin@example.com", password=generate_password_hash("AdminPass123"), is_admin=True
        )
        db.session.add(user)
        db.session.commit()

        assert user.is_admin is True

    def test_user_timestamps(self, test_user):
        """Test that user has creation timestamp."""
        assert test_user.created_at is not None
        assert isinstance(test_user.created_at, datetime)

    def test_get_id_lazily_generates_a_session_token(self, test_user):
        """New/existing users have no session_token until get_id() is
        first called (login time) - generated and persisted on demand
        rather than backfilled by migration, since every user logs in at
        some point regardless."""
        assert test_user.session_token is None
        composite_id = test_user.get_id()
        assert test_user.session_token is not None
        assert composite_id == f"{test_user.id}:{test_user.session_token}"

    def test_get_id_reuses_existing_token_on_subsequent_calls(self, test_user):
        """Calling get_id() twice must not rotate the token each time -
        only rotate_session_token() should change it, otherwise every
        request would invalidate the session that made it."""
        first = test_user.get_id()
        second = test_user.get_id()
        assert first == second

    def test_rotate_session_token_changes_the_value(self, test_user):
        test_user.get_id()  # establish an initial token
        original = test_user.session_token
        test_user.rotate_session_token()
        assert test_user.session_token != original
        assert test_user.session_token is not None

    def test_load_user_accepts_matching_token(self, app, test_user):
        from models.user import load_user
        from app import db

        composite_id = test_user.get_id()
        db.session.commit()

        loaded = load_user(composite_id)
        assert loaded is not None
        assert loaded.id == test_user.id

    def test_load_user_rejects_stale_token(self, app, test_user):
        """The actual mechanism behind the session-invalidation fix: once
        session_token is rotated, a session ID built from the *old* token
        must be rejected — this is what makes a password reset kill other
        sessions."""
        from models.user import load_user
        from app import db

        stale_composite_id = test_user.get_id()  # "device A" logs in
        db.session.commit()

        test_user.rotate_session_token()  # password reset elsewhere
        db.session.commit()

        assert load_user(stale_composite_id) is None

    def test_load_user_grandfathers_in_bare_numeric_id(self, app, test_user):
        """A session cookie issued before this feature existed (or by
        code that sets the session key directly rather than through
        get_id(), like this test suite's authenticated_client fixture)
        is a bare numeric ID with no ':' - honored once rather than
        force-logging out every already-signed-in user the moment this
        ships, by design (see load_user()'s docstring)."""
        from models.user import load_user

        loaded = load_user(str(test_user.id))
        assert loaded is not None
        assert loaded.id == test_user.id

    def test_load_user_rejects_garbage_id(self, app):
        from models.user import load_user

        assert load_user("not-a-real-id") is None
        assert load_user("99999:sometoken") is None


class TestTourPackageModel:
    """Test TourPackage model."""

    def test_package_creation(self, app):
        """Test creating a tour package."""
        from app import db

        package = TourPackage(
            title="Test Tour",
            description="A test tour",
            destination="Test Destination",
            duration_days=7,
            price=5000.00,
            currency="PHP",
            is_active=True,
        )
        db.session.add(package)
        db.session.commit()

        assert package.id is not None
        assert package.title == "Test Tour"

    def test_package_inactive(self, app):
        """Test inactive package."""
        from app import db

        package = TourPackage(
            title="Inactive Tour",
            description="An inactive tour",
            destination="Test",
            duration_days=3,
            price=1000.00,
            currency="PHP",
            is_active=False,
        )
        db.session.add(package)
        db.session.commit()

        assert package.is_active is False

    def test_package_currency(self, test_package):
        """Test package currency field."""
        assert test_package.currency == "PHP"


class TestAgentModel:
    """Test Agent model."""

    def test_agent_creation_defaults(self, app):
        """Test creating an agent relies on the right column defaults."""
        from app import db

        agent = Agent(name="Juan Dela Cruz", email="juan@travelworthyph.com")
        db.session.add(agent)
        db.session.commit()

        assert agent.id is not None
        assert agent.is_active is True
        assert agent.is_visa_agent is False
        assert agent.created_at is not None

    def test_agent_repr(self, app):
        """Test agent string representation."""
        from app import db

        agent = Agent(name="Juan Dela Cruz", email="juan@travelworthyph.com")
        db.session.add(agent)
        db.session.commit()

        assert "Juan Dela Cruz" in repr(agent)

    def test_package_assigned_agent_relationship(self, app):
        """Test TourPackage.assigned_agent resolves via the relationship,
        not just the raw assigned_agent_id foreign key."""
        from app import db

        agent = Agent(name="Juan Dela Cruz", email="juan@travelworthyph.com")
        db.session.add(agent)
        db.session.commit()

        package = TourPackage(
            title="Test Tour",
            description="A test tour",
            destination="Test Destination",
            duration_days=7,
            price=5000.00,
            currency="PHP",
            assigned_agent_id=agent.id,
        )
        db.session.add(package)
        db.session.commit()

        assert package.assigned_agent.name == "Juan Dela Cruz"
        assert package in agent.packages


class TestModelConstraints:
    """Test model constraints and validations."""

    def test_unique_email_constraint(self, app, test_user):
        """Test that email must be unique."""
        from app import db
        from sqlalchemy.exc import IntegrityError

        duplicate_user = User(
            name="Duplicate", email=test_user.email, password=generate_password_hash("Password123"), is_admin=False
        )
        db.session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_package_price_positive(self, app):
        """Test that package price can be zero or positive."""
        from app import db

        package = TourPackage(
            title="Free Tour", description="A free tour", destination="Free", duration_days=1, price=0.00, currency="PHP"
        )
        db.session.add(package)
        db.session.commit()

        assert package.price == 0.00


class TestWishlistItemModel:
    """Test WishlistItem model."""

    def test_save_package(self, app, test_user, test_package):
        """Test saving a package populates package_id and leaves visa_id unset."""
        from app import db

        item = WishlistItem(user_id=test_user.id, package_id=test_package.id)
        db.session.add(item)
        db.session.commit()

        assert item.id is not None
        assert item.visa_id is None
        assert isinstance(item.created_at, datetime)

    def test_save_visa(self, app, test_user):
        """Test saving a visa country populates visa_id and leaves package_id unset."""
        from app import db

        visa = VisaCountry(country_name="Japan", is_active=True)
        db.session.add(visa)
        db.session.commit()

        item = WishlistItem(user_id=test_user.id, visa_id=visa.id)
        db.session.add(item)
        db.session.commit()

        assert item.id is not None
        assert item.package_id is None

    def test_relationships_both_directions(self, app, test_user, test_package):
        """Test the user/package relationships resolve, not just the raw FKs."""
        from app import db

        item = WishlistItem(user_id=test_user.id, package_id=test_package.id)
        db.session.add(item)
        db.session.commit()

        assert item.user.id == test_user.id
        assert item.package.id == test_package.id
        assert item in test_user.wishlist_items
        assert item in test_package.wishlist_items

    def test_repr(self, app, test_user, test_package):
        """Test string representation."""
        from app import db

        item = WishlistItem(user_id=test_user.id, package_id=test_package.id)
        db.session.add(item)
        db.session.commit()

        assert f"package={test_package.id}" in repr(item)

    def test_duplicate_save_of_same_package_violates_unique_constraint(self, app, test_user, test_package):
        """Test a user can't save the same package twice."""
        from app import db
        from sqlalchemy.exc import IntegrityError

        db.session.add(WishlistItem(user_id=test_user.id, package_id=test_package.id))
        db.session.commit()
        db.session.add(WishlistItem(user_id=test_user.id, package_id=test_package.id))

        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_requires_exactly_one_target(self, app, test_user, test_package):
        """Test ck_wishlist_exactly_one_target rejects both-set and neither-set rows."""
        from app import db
        from sqlalchemy.exc import IntegrityError

        visa = VisaCountry(country_name="Korea", is_active=True)
        db.session.add(visa)
        db.session.commit()

        db.session.add(WishlistItem(user_id=test_user.id, package_id=test_package.id, visa_id=visa.id))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        db.session.add(WishlistItem(user_id=test_user.id))
        with pytest.raises(IntegrityError):
            db.session.commit()
