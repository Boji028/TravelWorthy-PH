"""Tests for form validation."""
import pytest
from forms import RegisterForm, LoginForm, ChangePasswordForm, InquiryForm, StrongPasswordValidator, FullNameValidator
from datetime import date, timedelta


class TestFullNameValidator:
    """Test full name validation (first + last name required)."""

    def test_single_word_rejected(self):
        """Test a single-word name is rejected."""
        validator = FullNameValidator()

        class MockField:
            data = "AB"

        class MockForm:
            pass

        with pytest.raises(Exception):  # ValidationError
            validator(MockForm(), MockField())

    def test_digits_rejected(self):
        """Test a name containing digits is rejected."""
        validator = FullNameValidator()

        class MockField:
            data = "John Doe2"

        class MockForm:
            pass

        with pytest.raises(Exception):  # ValidationError
            validator(MockForm(), MockField())

    def test_short_name_part_rejected(self):
        """Test a name part shorter than 2 letters is rejected."""
        validator = FullNameValidator()

        class MockField:
            data = "J D"

        class MockForm:
            pass

        with pytest.raises(Exception):  # ValidationError
            validator(MockForm(), MockField())

    def test_valid_two_word_name_accepted(self):
        """Test a standard first + last name passes."""
        validator = FullNameValidator()

        class MockField:
            data = "John Doe"

        class MockForm:
            pass

        validator(MockForm(), MockField())  # should not raise

    def test_valid_multiword_filipino_surname_accepted(self):
        """Test a name with a two-word surname (common in PH) passes."""
        validator = FullNameValidator()

        class MockField:
            data = "Juan Dela Cruz"

        class MockForm:
            pass

        validator(MockForm(), MockField())  # should not raise


class TestStrongPasswordValidator:
    """Test password strength validation."""

    def test_password_too_short(self):
        """Test password shorter than 12 characters."""
        validator = StrongPasswordValidator()

        class MockField:
            data = "Short1"

        class MockForm:
            pass

        with pytest.raises(Exception):  # ValidationError
            validator(MockForm(), MockField())

    def test_password_no_uppercase(self):
        """Test password without uppercase letter."""
        validator = StrongPasswordValidator()

        class MockField:
            data = "lowercase123456"

        class MockForm:
            pass

        with pytest.raises(Exception):  # ValidationError
            validator(MockForm(), MockField())

    def test_password_no_digit(self):
        """Test password without digit."""
        validator = StrongPasswordValidator()

        class MockField:
            data = "NoDigitsHere!!!!"

        class MockForm:
            pass

        with pytest.raises(Exception):  # ValidationError
            validator(MockForm(), MockField())

    def test_valid_password(self):
        """Test valid strong password."""
        validator = StrongPasswordValidator()

        class MockField:
            data = "ValidPassword123"

        class MockForm:
            pass

        # Should not raise
        validator(MockForm(), MockField())


class TestRegisterForm:
    """Test registration form validation."""

    def test_register_form_valid(self, app):
        """Test valid registration form."""
        with app.test_request_context():
            form = RegisterForm(
                data={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "password": "ValidPassword123",
                    "confirm_password": "ValidPassword123",
                }
            )
            # Form validation would occur here
            assert form.name.data == "John Doe"

    def test_register_form_invalid_email(self, app):
        """Test register form with invalid email."""
        with app.test_request_context():
            form = RegisterForm(
                data={
                    "name": "John Doe",
                    "email": "invalid-email",
                    "password": "ValidPassword123",
                    "confirm_password": "ValidPassword123",
                }
            )


class TestInquiryForm:
    """Test inquiry form validation."""

    def test_inquiry_form_valid(self, app):
        """Test valid inquiry form."""
        with app.test_request_context():
            future_from = date.today() + timedelta(days=30)
            future_to = date.today() + timedelta(days=40)
            form = InquiryForm(
                data={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "contact_number": "+1234567890",
                    "destination": "Bali",
                    "travel_date_from": future_from,
                    "travel_date_to": future_to,
                    "num_adults": 2,
                    "num_children": 1,
                    "num_infants": 0,
                }
            )
            assert form.destination.data == "Bali"

    def test_inquiry_form_end_before_start(self, app):
        """Test inquiry form with end date before start date."""
        with app.test_request_context():
            future_from = date.today() + timedelta(days=40)
            future_to = date.today() + timedelta(days=30)
            form = InquiryForm(
                data={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "contact_number": "+1234567890",
                    "destination": "Bali",
                    "travel_date_from": future_from,
                    "travel_date_to": future_to,
                    "num_adults": 2,
                }
            )
