"""Centralized form validation using Flask-WTF and WTForms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField,
    IntegerField, FloatField, SelectField, DateField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional,
    Regexp, NumberRange, ValidationError
)
from datetime import date
import re


def _strip(value):
    """WTForms filter: strip whitespace, safe for None."""
    return value.strip() if isinstance(value, str) else value



class StrongPasswordValidator:
    """Custom validator for password requirements (8+ chars, 1 uppercase, 1 digit)."""

    def __init__(self, message: str = 'Password must be at least 8 characters with 1 uppercase and 1 digit'):
        self.message = message

    def __call__(self, form, field):
        if len(field.data) < 8:
            raise ValidationError('Password must be at least 8 characters.')
        if not re.search(r'[A-Z]', field.data):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[0-9]', field.data):
            raise ValidationError('Password must contain at least one digit.')

class RegisterForm(FlaskForm):
    """User registration form with validation."""
    name = StringField('Full Name', validators=[
        DataRequired('Name is required'),
        Length(min=2, max=100, message='Name must be 2-100 characters')
    ])
    email = StringField('Email', filters=(_strip,), validators=[
        DataRequired('Email is required'),
        Email(message='Invalid email format', granular_message=False),
        Length(max=150, message='Email must be 150 characters or fewer'),
    ])
    phone = StringField('Phone', validators=[
        Optional(),
        Regexp(r'^\+?\d{7,15}$', message='Invalid phone number format (e.g. +639171234567)')
    ])
    password = PasswordField('Password', validators=[
        DataRequired('Password is required'),
        StrongPasswordValidator()
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired('Password confirmation is required'),
        EqualTo('password', message='Passwords must match')
    ])


class LoginForm(FlaskForm):
    """User login form with validation."""
    email = StringField('Email', filters=(_strip,), validators=[
        DataRequired('Email is required'),
        Email(message='Invalid email format', granular_message=False),
        Length(max=150, message='Email must be 150 characters or fewer'),
    ])
    password = PasswordField('Password', validators=[
        DataRequired('Password is required'),
        Length(max=128, message='Password must be 128 characters or fewer')
    ])
    remember = BooleanField('Remember Me')


class ChangePasswordForm(FlaskForm):
    """Change password form with validation."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired('Current password is required'),
        Length(max=128, message='Password must be 128 characters or fewer')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired('New password is required'),
        StrongPasswordValidator()
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired('Password confirmation is required'),
        EqualTo('new_password', message='Passwords must match')
    ])


class ContactForm(FlaskForm):
    """Contact message form with validation."""
    name = StringField('Name', validators=[
        DataRequired('Name is required'),
        Length(min=2, max=100, message='Name must be 2-100 characters')
    ])
    email = StringField('Email', filters=(_strip,), validators=[
        DataRequired('Email is required'),
        Email(message='Invalid email format', granular_message=False),
    ])
    subject = StringField('Subject', validators=[
        DataRequired('Subject is required'),
        Length(min=2, max=200, message='Subject must be 2-200 characters')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired('Message is required'),
        Length(min=1, max=5000, message='Message must be under 5000 characters')
    ])


class InquiryForm(FlaskForm):
    """Trip inquiry form with validation."""
    name = StringField('Full Name', validators=[
        DataRequired('Name is required'),
        Length(min=2, max=100, message='Name must be 2-100 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired('Email is required'),
        Email(message='Invalid email format', granular_message=False)
    ])
    contact_number = StringField('Contact Number', validators=[
        DataRequired('Contact number is required'),
        Regexp(r'^\+?1?\d{9,15}$', message='Invalid phone number format')
    ])
    destination = StringField('Destination', validators=[
        DataRequired('Destination is required'),
        Length(min=2, max=200, message='Destination must be 2-200 characters')
    ])
    travel_date_from = DateField('Travel From', validators=[
        DataRequired('Start date is required')
    ])
    travel_date_to = DateField('Travel To', validators=[
        DataRequired('End date is required')
    ])
    num_adults = IntegerField('Number of Adults', validators=[
        DataRequired('Number of adults is required'),
        NumberRange(min=1, max=100, message='Must be 1-100 adults')
    ])
    num_children = IntegerField('Number of Children', default=0, validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Must be 0-100 children')
    ])
    num_infants = IntegerField('Number of Infants', default=0, validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Must be 0-100 infants')
    ])
    special_requests = TextAreaField('Special Requests', validators=[
        Optional(),
        Length(max=2000, message='Special requests must be under 2000 characters')
    ])

    def validate_travel_date_from(self, field):
        if field.data and field.data <= date.today():
            raise ValidationError('Departure date must be in the future (not today).')

    def validate_travel_date_to(self, field):
        if field.data and self.travel_date_from.data:
            if field.data < self.travel_date_from.data:
                raise ValidationError('Return date must be on or after the departure date.')


class TourPackageForm(FlaskForm):
    """Tour package form for admin."""
    title = StringField('Package Title', validators=[
        DataRequired('Title is required'),
        Length(min=5, max=200, message='Title must be 5-200 characters')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired('Description is required'),
        Length(min=20, max=5000, message='Description must be 20-5000 characters')
    ])
    destination = StringField('Destination', validators=[
        DataRequired('Destination is required'),
        Length(min=2, max=150, message='Destination must be 2-150 characters')
    ])
    country_id = IntegerField('Country', validators=[Optional()])
    duration_days = IntegerField('Duration (days)', validators=[
        DataRequired('Duration is required'),
        NumberRange(min=1, max=365, message='Duration must be 1-365 days')
    ])
    price = FloatField('Price', validators=[
        DataRequired('Price is required'),
        NumberRange(min=0.01, message='Price must be greater than 0')
    ])
    currency = SelectField('Currency', choices=[('PHP', 'PHP'), ('USD', 'USD'), ('EUR', 'EUR')], default='PHP')
    inclusions = TextAreaField('Inclusions', validators=[
        Optional(),
        Length(max=2000, message='Inclusions must be under 2000 characters')
    ])
    exclusions = TextAreaField('Exclusions', validators=[
        Optional(),
        Length(max=2000, message='Exclusions must be under 2000 characters')
    ])
    image = FileField('Package Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Image files only (jpg, jpeg, png, gif, webp)')
    ])
