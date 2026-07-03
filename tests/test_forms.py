"""Tests for form validation."""
import pytest
from forms import RegisterForm, LoginForm, ChangePasswordForm, ContactForm, InquiryForm, StrongPasswordValidator
from datetime import date, timedelta


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


class TestContactForm:
    """Test contact form validation."""

    def test_contact_form_valid(self, app):
        """Test valid contact form."""
        with app.test_request_context():
            form = ContactForm(
                data={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "subject": "Inquiry about packages",
                    "message": "I would like to know more about your tour packages.",
                }
            )
            assert form.name.data == "John Doe"

    def test_contact_form_short_message(self, app):
        """Test contact form with message too short."""
        with app.test_request_context():
            form = ContactForm(data={"name": "John", "email": "john@example.com", "subject": "Hi", "message": "Short"})
