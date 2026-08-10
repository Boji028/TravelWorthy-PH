"""Wishlist routes for saving/unsaving packages and visa countries."""
from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import current_user, login_required

from app import db

wishlist_bp = Blueprint("wishlist", __name__)


def _login_required_response():
    """Toggle routes are called via fetch(), not real page navigation, so
    they can't rely on @login_required's default redirect - that returns
    HTML, which the caller's JSON parsing would choke on (see
    static/js/wishlist.js). Returning a real 401 with a login_url lets the
    frontend redirect the browser itself instead of silently failing."""
    return (
        jsonify(success=False, login_required=True, login_url=url_for("auth.login", next=request.referrer or "/")),
        401,
    )


@wishlist_bp.route("/toggle/package/<int:package_id>", methods=["POST"])
def toggle_package(package_id: int):
    """Save or unsave a tour package for the current user."""
    from models.package import TourPackage
    from models.wishlist import WishlistItem

    if not current_user.is_authenticated:
        return _login_required_response()

    existing = WishlistItem.query.filter_by(user_id=current_user.id, package_id=package_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify(success=True, saved=False)

    db.get_or_404(TourPackage, package_id)
    db.session.add(WishlistItem(user_id=current_user.id, package_id=package_id))
    db.session.commit()
    return jsonify(success=True, saved=True)


@wishlist_bp.route("/toggle/visa/<int:visa_id>", methods=["POST"])
def toggle_visa(visa_id: int):
    """Save or unsave a visa country entry for the current user."""
    from models.visa import VisaCountry
    from models.wishlist import WishlistItem

    if not current_user.is_authenticated:
        return _login_required_response()

    existing = WishlistItem.query.filter_by(user_id=current_user.id, visa_id=visa_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify(success=True, saved=False)

    db.get_or_404(VisaCountry, visa_id)
    db.session.add(WishlistItem(user_id=current_user.id, visa_id=visa_id))
    db.session.commit()
    return jsonify(success=True, saved=True)


@wishlist_bp.route("/")
@login_required
def my_wishlist():
    """The logged-in user's saved packages and visa countries, split into
    two lists for the template to render as separate sections."""
    from models.wishlist import WishlistItem

    items = WishlistItem.query.filter_by(user_id=current_user.id).order_by(WishlistItem.created_at.desc()).all()
    saved_packages = [item for item in items if item.package_id]
    saved_visas = [item for item in items if item.visa_id]
    return render_template("wishlist/my_wishlist.html", saved_packages=saved_packages, saved_visas=saved_visas)
