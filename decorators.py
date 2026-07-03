"""Authorization decorators for route protection."""
from functools import wraps
from typing import Callable, Any, TypeVar
from flask import redirect, url_for, flash
from flask_login import current_user, login_required

F = TypeVar("F", bound=Callable[..., Any])


def admin_required(f: F) -> F:
    """Restrict a route to admin users only.

    Chains @login_required first so unauthenticated requests are always
    redirected to the login page before the admin check runs.

    Usage:
        @admin_required
        def admin_route():
            return 'Admin only content'
    """

    @wraps(f)
    @login_required  # FIX: handles the unauthenticated redirect reliably
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)

    return decorated_function  # type: ignore[return-value]
