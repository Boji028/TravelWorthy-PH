"""Authentication routes — staff/admin login only.

Public self-registration, Google OAuth sign-in, and email verification
used to live here and have been removed: this app no longer has
customer accounts (guests can inquire and subscribe without one). Every
route below is for staff use. New staff logins are created from the
admin panel (see admin.add_user) rather than through a public form, and
the login page itself is deliberately not linked from the public nav
— reachable only at /staff-portal for whoever already knows the URL.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError

from app import db, limiter
from models.user import User
from forms import LoginForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from password_reset_service import PasswordResetService

auth_bp = Blueprint("auth", __name__)

@auth_bp.after_request
def keep_out_of_search_results(response):
    """Tell search engines not to index or follow any staff auth page."""
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@auth_bp.route("/staff-portal", methods=["GET", "POST"])
@limiter.limit(
    "5 per minute; 20 per hour",
    methods=["POST"],
    key_func=lambda: (request.form.get("email", request.remote_addr) or "unknown").lower(),
)
def login():
    """Staff login route with session management and error handling."""
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


@auth_bp.route("/logout")
@login_required
def logout():
    """Staff logout route."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Staff profile and password change route with error handling."""
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


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit(
    "5 per hour",
    methods=["POST"],
    key_func=lambda: (request.form.get("email", request.remote_addr) or "unknown").lower(),
)
def forgot_password():
    """Request a password reset link by email — staff use only."""
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
