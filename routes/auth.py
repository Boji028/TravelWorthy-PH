"""Authentication routes for user registration, login, and profile management."""
from typing import Union
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db, limiter
from oauth import oauth
from models.user import User
from forms import RegisterForm, LoginForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from email_verification_service import EmailVerificationService
from password_reset_service import PasswordResetService

auth_bp = Blueprint("auth", __name__)


def _email_verification_required() -> bool:
    """Return True when new users must verify email before logging in."""
    return current_app.config.get("REQUIRE_EMAIL_VERIFICATION", False)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration route with email validation and error handling."""
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=form.email.data.lower()).first()
            if existing_user:
                current_app.logger.info(f"Registration attempt with existing email: {form.email.data.lower()}")
                flash("Email already registered. Please login.", "warning")
                return redirect(url_for("auth.login"))

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
                    current_app.logger.warning(f"Verification email failed for {new_user.email}")
                    flash(
                        "Registration successful! However, the verification email "
                        "could not be sent. Use the resend link below or contact support.",
                        "warning",
                    )
                else:
                    flash(
                        "Registration successful! Please check your email to verify your account.",
                        "success",
                    )
                session["pending_verification_email"] = new_user.email
                return redirect(url_for("auth.pending_verification"))
            try:
                from email_service import send_user_registration_welcome

                send_user_registration_welcome(new_user)
            except Exception:
                pass
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("auth.login"))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error during registration: {e}", exc_info=True)
            flash("An account with this email already exists.", "danger")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during registration: {e}", exc_info=True)
            flash("Registration failed due to a database error. Please try again.", "danger")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error during registration: {e}", exc_info=True)
            flash("An unexpected error occurred. Please try again later.", "danger")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login route with session management and error handling."""
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data.lower()).first()

            if not user or not user.password or not check_password_hash(user.password, form.password.data):
                current_app.logger.warning(
                    f"Failed login attempt for email: {form.email.data.lower()} from IP: {request.remote_addr}"
                )
                flash("Invalid email or password.", "danger")
                return redirect(url_for("auth.login"))

            if _email_verification_required() and not user.email_verified:
                current_app.logger.warning(f"Login attempt with unverified email: {user.email}")
                flash(
                    "Please verify your email before logging in. " "Check your inbox for a verification link.",
                    "warning",
                )
                return redirect(url_for("auth.pending_verification", email=user.email))

            login_user(user, remember=form.remember.data)
            current_app.logger.info(f"User logged in: {user.email} from IP: {request.remote_addr}")

            next_page = request.args.get("next")
            # Reject anything that isn't a plain relative path: must start with /
            # and must not start with // or contain backslashes (browser open-redirect vectors).
            if next_page and not (next_page.startswith("/") and not next_page.startswith("//") and "\\" not in next_page):
                next_page = None

            flash(f"Welcome back, {user.name}!", "success")
            return redirect(next_page or url_for("main.home"))

        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during login: {e}", exc_info=True)
            flash("Login failed. Please try again.", "danger")
        except Exception as e:
            current_app.logger.error(f"Unexpected error during login: {e}", exc_info=True)
            flash("An unexpected error occurred. Please try again later.", "danger")

    return render_template("auth/login.html", form=form)


def _oauth_login(user):
    """Shared login step for both OAuth callbacks."""
    login_user(user, remember=True)
    current_app.logger.info(f"User logged in via {user.oauth_provider}: {user.email}")
    flash(f"Welcome back, {user.name}!", "success")
    return redirect(url_for("main.home"))


@auth_bp.route("/google/login")
def google_login():
    if "google" not in oauth._clients:
        flash("Google sign-in is not configured yet.", "danger")
        return redirect(url_for("auth.login"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    if "google" not in oauth._clients:
        flash("Google sign-in is not configured yet.", "danger")
        return redirect(url_for("auth.login"))
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or oauth.google.userinfo()
    except Exception as e:
        current_app.logger.error(f"Google OAuth callback failed: {e}", exc_info=True)
        flash("Google sign-in failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    google_id = userinfo.get("sub")
    email = (userinfo.get("email") or "").lower()
    email_verified = userinfo.get("email_verified", False)
    name = userinfo.get("name") or email.split("@")[0]

    if not google_id or not email:
        flash("Google did not return the required account details.", "danger")
        return redirect(url_for("auth.login"))

    try:
        # 1. Already linked to this Google identity — just log in.
        user = User.query.filter_by(oauth_provider="google", oauth_id=google_id).first()
        if user:
            return _oauth_login(user)

        # 2. Email matches an existing account. Google verifies email
        #    ownership, so it's safe to auto-link.
        existing = User.query.filter_by(email=email).first()
        if existing:
            if email_verified:
                existing.oauth_provider = "google"
                existing.oauth_id = google_id
                db.session.commit()
                current_app.logger.info(f"Linked Google identity to existing account: {email}")
                return _oauth_login(existing)
            flash(
                "An account with this email already exists. " "Please log in with your password first.",
                "warning",
            )
            return redirect(url_for("auth.login"))

        # 3. Brand new account.
        new_user = User(
            name=name,
            email=email,
            password=None,
            oauth_provider="google",
            oauth_id=google_id,
            email_verified=email_verified,
        )
        db.session.add(new_user)
        db.session.commit()
        current_app.logger.info(f"New user registered via Google: {email}")
        return _oauth_login(new_user)

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during Google OAuth: {e}", exc_info=True)
        flash("Sign-in failed due to a database error. Please try again.", "danger")
        return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile and password change route with error handling."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            if not current_user.password:
                flash(
                    "This account signs in with Google and has no password to change.",
                    "warning",
                )
                return redirect(url_for("auth.profile"))
            
            if not check_password_hash(current_user.password, form.current_password.data):
                current_app.logger.warning(f"Failed password change attempt for user: {current_user.email}")
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("auth.profile"))

            if check_password_hash(current_user.password, form.new_password.data):
                flash("New password must be different from your current password.", "danger")
                return redirect(url_for("auth.profile"))

            current_user.password = generate_password_hash(form.new_password.data)
            # Same reasoning as the forgot-password reset flow: rotate to
            # invalidate any other active session for this account. Then
            # immediately re-login so *this* session (the one used to
            # make the change) stays valid — otherwise the person who
            # just changed their own password would find themselves
            # logged out by their own action. login_user() needs the
            # real User object, not the current_user LocalProxy — passing
            # the proxy itself causes infinite recursion inside
            # flask_login's internals.
            current_user.rotate_session_token()
            db.session.commit()
            login_user(current_user._get_current_object(), remember=True)
            current_app.logger.info(f"Password changed for user: {current_user.email}")
            flash("Password changed successfully!", "success")
            return redirect(url_for("auth.profile"))

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error changing password for {current_user.email}: {e}", exc_info=True)
            flash("Password change failed due to a database error. Please try again.", "danger")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error changing password: {e}", exc_info=True)
            flash("An unexpected error occurred. Please try again later.", "danger")

    return render_template("auth/profile.html", form=form)


@auth_bp.route("/pending-verification")
def pending_verification():
    """Show page for user to verify their email."""
    email = session.pop("pending_verification_email", request.args.get("email", ""))
    return render_template("auth/pending_verification.html", email=email)


@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    """Verify user email with token."""
    success, message, user = EmailVerificationService.verify_email(token)

    if success:
        flash(message, "success")
        return redirect(url_for("auth.login"))
    else:
        flash(message, "danger")
        # Get email from token if possible
        from models.email_verification import EmailVerificationToken

        token_obj = EmailVerificationToken.query.filter_by(token=token).first()
        email = token_obj.email if token_obj else ""
        return redirect(url_for("auth.pending_verification", email=email))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
@limiter.limit("5 per hour", key_func=lambda: (request.form.get("email", request.remote_addr) or "unknown").lower())
def resend_verification():
    """Resend verification email to user."""
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        if not email:
            flash("Please provide an email address.", "danger")
            return redirect(url_for("auth.resend_verification"))

        success, message = EmailVerificationService.resend_verification_email(email)
        flash(message, "success" if success else "danger")

        if success:
            session["pending_verification_email"] = email
            return redirect(url_for("auth.pending_verification"))

    email = request.args.get("email", "")
    return render_template("auth/resend_verification.html", email=email)

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour", key_func=lambda: (request.form.get("email", request.remote_addr) or "unknown").lower())
def forgot_password():
    """Request a password reset link by email."""
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        success, message = PasswordResetService.request_reset(form.email.data.lower())
        flash(message, "success" if success else "danger")
        if success:
            return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Set a new password using a valid reset token."""
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    from models.password_reset import PasswordResetToken

    token_obj = PasswordResetToken.get_valid_token(token)
    if not token_obj:
        flash("This reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        success, message, user = PasswordResetService.reset_password(token, form.password.data)
        flash(message, "success" if success else "danger")
        if success:
            return redirect(url_for("auth.login"))
        return redirect(url_for("auth.forgot_password"))

    return render_template("auth/reset_password.html", form=form, token=token)
