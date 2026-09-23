"""Admin CRUD for Offers, kept out of admin.py since that file is already very large."""
from decimal import Decimal, InvalidOperation
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from app import db
from decorators import admin_required
from utils import delete_old_image
from image_service import ImageUploadService, ImageUploadException
from models.offer import Offer, OFFER_CATEGORIES
from routes.admin import admin_bp


def _apply_offer_form(offer: Offer):
    """Validate the posted form and copy it onto offer; returns an error message or None."""
    form = request.form
    title = form.get("title", "").strip()
    if not title:
        return "Title is required."

    category = form.get("category", "")
    if category not in OFFER_CATEGORIES:
        return "Please pick a valid category."

    price = None
    if form.get("price", "").strip():
        try:
            price = Decimal(form["price"].strip())
        except InvalidOperation:
            return "Price must be a number."
        if price < 0:
            return "Price cannot be negative."

    min_pax = None
    if form.get("min_pax", "").strip():
        try:
            min_pax = int(form["min_pax"])
        except ValueError:
            return "Minimum group size must be a whole number."
        if min_pax < 1:
            return "Minimum group size must be at least 1."

    # Photo last, since a replaced upload deletes the old file from storage.
    new_image = None
    image_url = form.get("image_url", "").strip()
    upload = request.files.get("image")
    if image_url.startswith("https://"):
        new_image = image_url
    elif upload and upload.filename:
        try:
            new_image = ImageUploadService.upload_and_compress(upload, "offer")["path"]
        except ImageUploadException as e:
            return f"Photo upload failed: {e}"

    if new_image and new_image != offer.image:
        delete_old_image(offer.image, current_app.config["UPLOAD_FOLDER"])
        offer.image = new_image

    offer.title = title[:150]
    offer.category = category
    offer.summary = form.get("summary", "").strip()[:300] or None
    offer.description = form.get("description", "").strip() or None
    offer.price = price
    offer.min_pax = min_pax
    offer.is_active = form.get("is_active") == "on"
    return None


@admin_bp.route("/offers")
@admin_required
def offer_list():
    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template("admin/offers.html", offers=offers)


@admin_bp.route("/offers/toggle-active/<int:offer_id>", methods=["POST"])
@admin_required
def toggle_offer_active(offer_id):
    offer = db.get_or_404(Offer, offer_id)
    offer.is_active = not offer.is_active
    db.session.commit()
    return jsonify(success=True, is_active=offer.is_active)


@admin_bp.route("/offers/add", methods=["GET", "POST"])
@admin_required
def offer_add():
    offer = Offer()
    if request.method == "POST":
        error = _apply_offer_form(offer)
        if error:
            flash(error, "danger")
            return render_template("admin/offer_form.html", offer=None, form=request.form, categories=OFFER_CATEGORIES)
        db.session.add(offer)
        db.session.commit()
        flash(f"{offer.title} added!", "success")
        return redirect(url_for("admin.offer_list"))
    return render_template("admin/offer_form.html", offer=None, form={}, categories=OFFER_CATEGORIES)


@admin_bp.route("/offers/edit/<int:offer_id>", methods=["GET", "POST"])
@admin_required
def offer_edit(offer_id):
    offer = db.get_or_404(Offer, offer_id)
    if request.method == "POST":
        error = _apply_offer_form(offer)
        if error:
            db.session.rollback()
            flash(error, "danger")
            return redirect(url_for("admin.offer_edit", offer_id=offer_id))
        db.session.commit()
        flash(f"{offer.title} updated!", "success")
        return redirect(url_for("admin.offer_list"))
    return render_template("admin/offer_form.html", offer=offer, form={}, categories=OFFER_CATEGORIES)


@admin_bp.route("/offers/remove-image/<int:offer_id>", methods=["POST"])
@admin_required
def remove_offer_image(offer_id):
    offer = db.get_or_404(Offer, offer_id)
    delete_old_image(offer.image, current_app.config["UPLOAD_FOLDER"])
    offer.image = None
    db.session.commit()
    flash("Photo removed.", "info")
    return redirect(url_for("admin.offer_edit", offer_id=offer_id))


@admin_bp.route("/offers/delete/<int:offer_id>", methods=["POST"])
@admin_required
def offer_delete(offer_id):
    offer = db.get_or_404(Offer, offer_id)
    delete_old_image(offer.image, current_app.config["UPLOAD_FOLDER"])
    db.session.delete(offer)
    db.session.commit()
    flash("Offer deleted.", "info")
    return redirect(url_for("admin.offer_list"))
