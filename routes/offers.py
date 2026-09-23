"""Public Offers pages - group deals like corporate incentives, team building and field trips."""
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from sqlalchemy.exc import SQLAlchemyError
from app import db, limiter
from models.offer import Offer, OFFER_CATEGORIES
from models.inquiry import Inquiry
from constants import InquiryStatus
from forms import OfferInquiryForm

offers_bp = Blueprint("offers", __name__)

# Prefix that tags an Inquiry as coming from an Offer, same idea as "[FOR VISA]".
OFFER_TAG = "[FOR OFFER]"


@offers_bp.route("/")
def offer_list():
    offers = Offer.query.filter_by(is_active=True).order_by(Offer.created_at.desc()).all()
    # Only show pills for categories that actually have offers.
    used = {o.category for o in offers}
    categories = [c for c in OFFER_CATEGORIES if c in used]
    return render_template("offers/list.html", offers=offers, categories=categories)


@offers_bp.route("/<int:offer_id>", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def offer_detail(offer_id):
    offer = Offer.query.filter_by(id=offer_id, is_active=True).first_or_404()
    form = OfferInquiryForm()

    if form.validate_on_submit():
        notes = [OFFER_TAG]
        if form.organization.data:
            notes.append(f"Organization: {form.organization.data}")
        if form.special_requests.data:
            notes.append(form.special_requests.data.strip())
        try:
            inquiry = Inquiry(
                name=form.name.data,
                email=form.email.data.lower(),
                contact_number=form.contact_number.data,
                destination=offer.title[:200],
                travel_date_from=form.travel_date_from.data,
                travel_date_to=form.travel_date_to.data,
                num_adults=form.num_adults.data,
                special_requests="\n".join(notes),
                inquiry_type="offer",
                status=InquiryStatus.NEW.value,
                privacy_consent=True,
                privacy_consent_at=datetime.now(timezone.utc),
            )
            db.session.add(inquiry)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"DB error creating offer inquiry: {e}", exc_info=True)
            flash("Database error occurred. Please try again.", "danger")
            return render_template("offers/detail.html", offer=offer, form=form)

        try:
            from notification_service import notify_inquiry_created, notify_admins_new_inquiry

            notify_inquiry_created(inquiry)
            notify_admins_new_inquiry(inquiry)
            db.session.commit()
        except Exception as notif_err:
            db.session.rollback()
            current_app.logger.warning(f"In-app notification failed for inquiry #{inquiry.id}: {notif_err}", exc_info=True)

        from email_service import send_inquiry_emails_async

        base_url = current_app.config.get("SITE_URL") or request.host_url
        send_inquiry_emails_async(inquiry.id, base_url)
        return redirect(url_for("main.track_inquiry", reference_number=inquiry.reference_number))

    return render_template("offers/detail.html", offer=offer, form=form)
