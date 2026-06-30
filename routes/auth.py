"""Authentication routes for user registration, login, and profile management."""
from typing import Union
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db, limiter
from models.user import User
from forms import RegisterForm, LoginForm, ChangePasswordForm
from email_verification_service import EmailVerificationService

auth_bp = Blueprint('auth', __name__)


def _email_verification_required() -> bool:
    """Return True when new users must verify email before logging in."""
    return current_app.config.get('REQUIRE_EMAIL_VERIFICATION', False)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register():
    """User registration route with email validation and error handling."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=form.email.data.lower()).first()
            if existing_user:
                current_app.logger.info(f"Registration attempt with existing email: {form.email.data.lower()}")
                flash('Email already registered. Please login.', 'warning')
                return redirect(url_for('auth.login'))

            verification_required = _email_verification_required()
            new_user = User(
                name=form.name.data,
                email=form.email.data.lower(),
                phone=form.phone.data,
                password=generate_password_hash(form.password.data),
                email_verified=not verification_required,
            )
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.info(f"New user registered: {new_user.email}")

            if verification_required:
                token = EmailVerificationService.create_verification_token(
                    new_user.id,
                    new_user.email,
                    expires_in_hours=24,
                )
                if not EmailVerificationService.send_verification_email(
                    new_user.email,
                    new_user.name,
                    token,
                    is_resend=False,
                    expires_in_hours=24,
                ):
                    current_app.logger.warning(
                        f"Verification email failed for {new_user.email}"
                    )
                    flash(
                        'Registration successful! However, the verification email '
                        'could not be sent. Use the resend link below or contact support.',
                        'warning',
                    )
                else:
                    flash(
                        'Registration successful! Please check your email to verify your account.',
                        'success',
                    )
                session['pending_verification_email'] = new_user.email
                return redirect(url_for('auth.pending_verification'))
            try:
                from email_service import send_user_registration_welcome
                send_user_registration_welcome(new_user)
            except Exception:
                pass
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error during registration: {e}", exc_info=True)
            flash('An account with this email already exists.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during registration: {e}", exc_info=True)
            flash('Registration failed due to a database error. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error during registration: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again later.', 'danger')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """User login route with session management and error handling."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data.lower()).first()

            if not user or not check_password_hash(user.password, form.password.data):
                current_app.logger.warning(f"Failed login attempt for email: {form.email.data.lower()} from IP: {request.remote_addr}")
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('auth.login'))

            if _email_verification_required() and not user.email_verified:
                current_app.logger.warning(f"Login attempt with unverified email: {user.email}")
                flash(
                    'Please verify your email before logging in. '
                    'Check your inbox for a verification link.',
                    'warning',
                )
                return redirect(url_for('auth.pending_verification', email=user.email))

            login_user(user, remember=form.remember.data)
            current_app.logger.info(f"User logged in: {user.email} from IP: {request.remote_addr}")
            
            next_page = request.args.get('next')
            # Reject anything that isn't a plain relative path: must start with /
            # and must not start with // or contain backslashes (browser open-redirect vectors).
            if next_page and not (
                next_page.startswith('/')
                and not next_page.startswith('//')
                and '\\' not in next_page
            ):
                next_page = None
            
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page or url_for('main.home'))
        
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during login: {e}", exc_info=True)
            flash('Login failed. Please try again.', 'danger')
        except Exception as e:
            current_app.logger.error(f"Unexpected error during login: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again later.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile and password change route with error handling."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            if not check_password_hash(current_user.password, form.current_password.data):
                current_app.logger.warning(f"Failed password change attempt for user: {current_user.email}")
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('auth.profile'))

            if check_password_hash(current_user.password, form.new_password.data):
                flash('New password must be different from your current password.', 'danger')
                return redirect(url_for('auth.profile'))

            current_user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            current_app.logger.info(f"Password changed for user: {current_user.email}")
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error changing password for {current_user.email}: {e}", exc_info=True)
            flash('Password change failed due to a database error. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error changing password: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again later.', 'danger')

    return render_template('auth/profile.html', form=form)


@auth_bp.route('/pending-verification')
def pending_verification():
    """Show page for user to verify their email."""
    email = session.pop('pending_verification_email', request.args.get('email', ''))
    return render_template('auth/pending_verification.html', email=email)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify user email with token."""
    success, message, user = EmailVerificationService.verify_email(token)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('auth.login'))
    else:
        flash(message, 'danger')
        # Get email from token if possible
        from models.email_verification import EmailVerificationToken
        token_obj = EmailVerificationToken.query.filter_by(token=token).first()
        email = token_obj.email if token_obj else ''
        return redirect(url_for('auth.pending_verification', email=email))


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
@limiter.limit("5 per hour", key_func=lambda: request.form.get('email', request.remote_addr).lower())
def resend_verification():
    """Resend verification email to user."""
    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        if not email:
            flash('Please provide an email address.', 'danger')
            return redirect(url_for('auth.resend_verification'))

        success, message = EmailVerificationService.resend_verification_email(email)
        flash(message, 'success' if success else 'danger')

        if success:
            session['pending_verification_email'] = email
            return redirect(url_for('auth.pending_verification'))

    email = request.args.get('email', '')
    return render_template('auth/resend_verification.html', email=email)
