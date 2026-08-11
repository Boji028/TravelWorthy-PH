"""Package routes for tour listing, details, and visa information."""
from typing import Union
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from flask_sqlalchemy.pagination import Pagination

from app import db
from models.package import TourPackage
from models.country import Country
from models.continent import Continent
from models.visa import VisaCountry

packages_bp = Blueprint("packages", __name__)


class _ShuffledPagination(Pagination):
    """Paginate a pre-shuffled list of IDs instead of issuing an
    ORDER BY on the query. A SQL-level ORDER BY RANDOM() reshuffles on
    every single query, so page 2 fetched independently from page 1 would
    show an unrelated random slice — packages could repeat across pages
    or never appear at all. Shuffling the id list once in Python and
    paginating that list keeps a page 2 request consistent with whatever
    page 1 showed for the same shuffle seed.
    """

    def _query_items(self) -> list:
        all_ids: list[int] = self._query_args["all_ids"]
        offset = self._query_offset
        page_ids = all_ids[offset : offset + self.per_page]
        if not page_ids:
            return []
        rows = (
            TourPackage.query.options(selectinload(TourPackage.images))
            .filter(TourPackage.id.in_(page_ids))
            .all()
        )
        by_id = {pkg.id: pkg for pkg in rows}
        return [by_id[pid] for pid in page_ids if pid in by_id]

    def _query_count(self) -> int:
        return len(self._query_args["all_ids"])


def _can_review_package(user_id: int, package_id: int) -> bool:
    """A user can review a package once they have a confirmed or closed
    booking (Inquiry) for it. Shared by package_detail() (to decide
    whether to render the review form at all) and submit_review() (to
    enforce it server-side) so the rule can't drift out of sync between
    the two — the earlier bug was exactly this: submit_review() enforced
    it, package_detail() didn't know about it at all.
    """
    from models.inquiry import Inquiry
    from constants import InquiryStatus

    return (
        Inquiry.query.filter(
            Inquiry.user_id == user_id,
            Inquiry.package_id == package_id,
            Inquiry.status.in_([InquiryStatus.CONFIRMED.value, InquiryStatus.CLOSED.value]),
        ).first()
        is not None
    )


@packages_bp.route("/")
def list_packages() -> Union[str, object]:
    """List tour packages with filtering options.

    Query parameters:
        - destination: Filter by destination name
        - country_id: Filter by country
        - continent_id: Filter by continent
        - duration: Filter by duration days
        - page: Pagination page number
    """
    destination: str = request.args.get("destination", "")
    country_id: int = request.args.get("country_id", type=int)
    continent_id: int = request.args.get("continent_id", type=int)
    package_type: str = request.args.get("package_type", "").strip()

    query = TourPackage.query.options(selectinload(TourPackage.images)).filter_by(is_active=True)

    if package_type in ("domestic", "international"):
        query = query.filter_by(package_type=package_type)

    if country_id:
        query = query.filter_by(country_id=country_id)
    elif continent_id:
        # Use subquery instead of Python loop to avoid N+1
        query = query.filter(
            TourPackage.country_id.in_(db.session.query(Country.id).filter_by(continent_id=continent_id, is_active=True))
        )

    if destination:
        query = query.filter(TourPackage.destination.ilike(f"%{destination}%"))

    duration: int = request.args.get("duration", type=int)

    if duration:
        query = query.filter(TourPackage.duration_days == duration)

    page: int = request.args.get("page", 1, type=int)

    # Random order, but stable per browsing session: an AJAX pagination
    # or filter request reuses the seed already in the session so page 2,
    # 3, etc. line up with what page 1 showed. Only a fresh (non-AJAX)
    # visit to this page gets a newly rolled seed, so the order changes
    # each time someone actually navigates here, without breaking
    # mid-browse pagination.
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if not is_ajax or "packages_shuffle_seed" not in session:
        session["packages_shuffle_seed"] = random.randint(0, 2**31 - 1)
    shuffle_seed = session["packages_shuffle_seed"]

    all_ids = [row.id for row in query.with_entities(TourPackage.id).all()]
    random.Random(shuffle_seed).shuffle(all_ids)

    packages = _ShuffledPagination(page=page, per_page=9, error_out=False, all_ids=all_ids)

    # Load related continent/country data to prevent N+1 queries
    continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
    active_continent = db.session.get(Continent, continent_id) if continent_id else None
    active_country = db.session.get(Country, country_id) if country_id else None

    from models.wishlist import WishlistItem

    saved_package_ids = WishlistItem.saved_ids(current_user.id, WishlistItem.package_id) if current_user.is_authenticated else set()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(
            "packages/list_ajax.html",
            packages=packages.items,
            pagination=packages,
            continent_id=continent_id,
            country_id=country_id,
            destination=destination or None,
            package_type=package_type or None,
            saved_package_ids=saved_package_ids,
        )

    return render_template(
        "packages/list.html",
        packages=packages.items,
        pagination=packages,
        continents=continents,
        active_continent=active_continent,
        active_country=active_country,
        package_type=package_type,
        saved_package_ids=saved_package_ids,
    )


@packages_bp.route("/<int:package_id>")
def package_detail(package_id: int) -> str:
    from models.package_review import PackageReview
    from models.wishlist import WishlistItem
    from flask_login import current_user

    package = TourPackage.query.filter_by(id=package_id, is_active=True).first_or_404()
    reviews = (
        PackageReview.query.options(selectinload(PackageReview.user))
        .filter_by(package_id=package_id)
        .order_by(PackageReview.created_at.desc())
        .all()
    )
    avg_result = db.session.query(func.avg(PackageReview.rating)).filter_by(package_id=package_id).scalar()
    avg_rating = round(float(avg_result), 1) if avg_result else None
    user_review = None
    can_review = False
    if current_user.is_authenticated:
        user_review = PackageReview.query.filter_by(package_id=package_id, user_id=current_user.id).first()
        # Same eligibility check submit_review() enforces server-side —
        # computed here too so the template can show the right state
        # (form vs. "book this trip first" message) instead of only
        # finding out on submit, after already writing a review.
        can_review = _can_review_package(current_user.id, package_id)
    # Build image list for the full-screen photo viewer
    all_images = []
    if package.image and package.image != "default_tour.jpg":
        all_images.append(package.image)
    for img in package.images:
        all_images.append(img.path)

    is_saved = (
        current_user.is_authenticated
        and WishlistItem.query.filter_by(user_id=current_user.id, package_id=package_id).first() is not None
    )

    # Same package_type (domestic/international) rather than country_id,
    # since country_id is only set on some packages — package_type is
    # always present and guaranteed comparable.
    related_packages = (
        TourPackage.query.filter(
            TourPackage.id != package_id,
            TourPackage.is_active.is_(True),
            TourPackage.package_type == package.package_type,
        )
        .order_by(func.random())
        .limit(3)
        .all()
    )
    saved_package_ids = (
        WishlistItem.saved_ids(current_user.id, WishlistItem.package_id)
        if current_user.is_authenticated
        else set()
    )

    return render_template(
        "packages/detail.html",
        package=package,
        reviews=reviews,
        avg_rating=avg_rating,
        user_reviewed=user_review is not None,
        user_review=user_review,
        can_review=can_review,
        all_images=all_images,
        is_saved=is_saved,
        related_packages=related_packages,
        saved_package_ids=saved_package_ids,
    )


@packages_bp.route("/<int:package_id>/review", methods=["POST"])
@login_required
def submit_review(package_id: int):
    from models.package_review import PackageReview
    from app import db

    package = TourPackage.query.filter_by(id=package_id, is_active=True).first_or_404()

    if not _can_review_package(current_user.id, package_id):
        flash("You can only review packages you have a confirmed booking for.", "warning")
        return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")

    existing = PackageReview.query.filter_by(package_id=package_id, user_id=current_user.id).first()
    if existing:
        flash("You have already reviewed this package.", "warning")
        return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")

    try:
        rating = int(request.form.get("rating", ""))
        if rating < 1 or rating > 5:
            raise ValueError("out of range")
    except (ValueError, TypeError):
        flash("Please select a rating between 1 and 5 stars.", "danger")
        return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")

    message = request.form.get("message", "").strip()
    if not message:
        flash("Please write something in your review.", "danger")
        return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")

    review = PackageReview(package_id=package_id, user_id=current_user.id, rating=rating, message=message)
    db.session.add(review)
    db.session.commit()
    flash("Thank you for your review!", "success")
    return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")


@packages_bp.route("/<int:package_id>/review/edit", methods=["POST"])
@login_required
def edit_review(package_id: int):
    """Update the current user's existing review for this package."""
    from models.package_review import PackageReview
    from app import db

    review = PackageReview.query.filter_by(package_id=package_id, user_id=current_user.id).first_or_404()

    try:
        rating = int(request.form.get("rating", ""))
        if rating < 1 or rating > 5:
            raise ValueError("out of range")
    except (ValueError, TypeError):
        flash("Please select a rating between 1 and 5 stars.", "danger")
        return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")

    message = request.form.get("message", "").strip()
    if not message:
        flash("Please write something in your review.", "danger")
        return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")

    review.rating = rating
    review.message = message
    db.session.commit()
    flash("Your review has been updated.", "success")
    return redirect(url_for("packages.package_detail", package_id=package_id) + "#s-reviews")


@packages_bp.route("/autocomplete")
def autocomplete() -> str:
    """Autocomplete endpoint for destination and country search."""
    q: str = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])

    results: list = []

    # Query for package destinations
    packages = TourPackage.query.filter(TourPackage.is_active == True, TourPackage.destination.ilike(f"%{q}%")).limit(5).all()

    for p in packages:
        if p.destination not in [r["name"] for r in results]:
            results.append({"name": p.destination})

    # Query for countries
    countries = Country.query.filter(Country.is_active == True, Country.name.ilike(f"%{q}%")).limit(3).all()

    for c in countries:
        if c.name not in [r["name"] for r in results]:
            results.append({"name": c.name})

    return jsonify(results[:6])


@packages_bp.route("/visa")
def visa() -> str:
    """Display visa requirements by country."""
    from models.wishlist import WishlistItem

    countries = VisaCountry.query.filter_by(is_active=True).order_by(VisaCountry.country_name).all()
    saved_visa_ids = WishlistItem.saved_ids(current_user.id, WishlistItem.visa_id) if current_user.is_authenticated else set()
    return render_template("packages/visa.html", countries=countries, saved_visa_ids=saved_visa_ids)


@packages_bp.route("/visa/country/<int:visa_id>/requirements")
def visa_requirements(visa_id: int) -> str:
    """Display visa requirements for a specific country.

    Args:
        visa_id: ID of the visa country record
    """
    country = db.get_or_404(VisaCountry, visa_id)
    return jsonify(
        {
            "id": country.id,
            "name": country.country_name,
            "flag_emoji": country.flag_emoji or "",
            "requirements": country.requirements_pdf or "",
        }
    )
