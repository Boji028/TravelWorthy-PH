"""Admin CRUD for Offers, kept out of admin.py since that file is already very large."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from app import db
from decorators import admin_required
from utils import delete_old_image
from image_service import ImageUploadService, ImageUploadException
from models.offer import Offer, OfferImage, OfferDate, OFFER_CATEGORIES
from routes.admin import admin_bp


def _pick_image(url_field: str, file_field: str, folder: str):
    """Return (new_path, error) for a single-image field; direct Cloudinary URL wins over a raw file."""
    url = request.form.get(url_field, "").strip()
    if url.startswith("https://"):
        return url, None
    upload = request.files.get(file_field)
    if upload and upload.filename:
        try:
            return ImageUploadService.upload_and_compress(upload, folder)["path"], None
        except ImageUploadException as e:
            return None, f"Upload failed: {e}"
    return None, None


def _parse_dates():
    """Return (list of OfferDate, error) from the repeatable date rows."""
    starts = request.form.getlist("offer_date_start")
    ends = request.form.getlist("offer_date_end")
    notes = request.form.getlist("offer_date_note")
    rows = []
    for i, raw in enumerate(starts):
        if not raw.strip():
            continue
        try:
            start = datetime.strptime(raw.strip(), "%Y-%m-%d").date()
            raw_end = ends[i].strip() if i < len(ends) else ""
            end = datetime.strptime(raw_end, "%Y-%m-%d").date() if raw_end else None
        except ValueError:
            return None, "One of the dates is not valid."
        if end and end < start:
            return None, "An end date is before its start date."
        note = notes[i].strip()[:100] if i < len(notes) else ""
        rows.append(OfferDate(date=start, end_date=end, note=note or None))
    return rows, None


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

    coords = []
    for name, limit in (("latitude", 90), ("longitude", 180)):
        raw = form.get(name, "").strip()
        try:
            value = float(raw) if raw else None
        except ValueError:
            return f"{name.title()} must be a number."
        if value is not None and not -limit <= value <= limit:
            return f"{name.title()} must be between -{limit} and {limit}."
        coords.append(value)
    if (coords[0] is None) != (coords[1] is None):
        return "Enter both latitude and longitude, or leave both blank."

    dates, error = _parse_dates()
    if error:
        return error

    # Photos last, since a replaced upload deletes the old file from storage.
    new_image, error = _pick_image("image_url", "image", "offer")
    if error:
        return error
    new_flier, error = _pick_image("flier_image_url", "flier_image", "offer_flier")
    if error:
        return error

    for field, new_path in (("image", new_image), ("flier_image", new_flier)):
        old_path = getattr(offer, field)
        if new_path and new_path != old_path:
            delete_old_image(old_path, current_app.config["UPLOAD_FOLDER"])
            setattr(offer, field, new_path)

    next_order = len(offer.images)
    for url in form.getlist("new_gallery_urls"):
        if url.startswith("https://"):
            offer.images.append(OfferImage(path=url, order=next_order))
            next_order += 1

    offer.dates = dates

    offer.title = title[:150]
    offer.category = category
    offer.summary = form.get("summary", "").strip()[:300] or None
    offer.description = form.get("description", "").strip() or None
    offer.price = price
    offer.min_pax = min_pax
    offer.duration = form.get("duration", "").strip()[:50] or None
    offer.location = form.get("location", "").strip()[:200] or None
    offer.latitude, offer.longitude = coords
    offer.highlights = form.get("highlights", "").strip() or None
    offer.inclusions = form.get("inclusions", "").strip() or None
    offer.exclusions = form.get("exclusions", "").strip() or None
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


@admin_bp.route("/offers/remove-image/<int:offer_id>/<field>", methods=["POST"])
@admin_required
def remove_offer_image(offer_id, field):
    if field not in ("image", "flier_image"):
        return jsonify(success=False), 400
    offer = db.get_or_404(Offer, offer_id)
    delete_old_image(getattr(offer, field), current_app.config["UPLOAD_FOLDER"])
    setattr(offer, field, None)
    db.session.commit()
    flash("Flier removed." if field == "flier_image" else "Photo removed.", "info")
    return redirect(url_for("admin.offer_edit", offer_id=offer_id))


@admin_bp.route("/offers/gallery/delete/<int:image_id>", methods=["POST"])
@admin_required
def delete_offer_gallery_image(image_id):
    img = db.get_or_404(OfferImage, image_id)
    delete_old_image(img.path, current_app.config["UPLOAD_FOLDER"])
    db.session.delete(img)
    db.session.commit()
    return jsonify(success=True)


@admin_bp.route("/offers/delete/<int:offer_id>", methods=["POST"])
@admin_required
def offer_delete(offer_id):
    offer = db.get_or_404(Offer, offer_id)
    for path in [offer.image, offer.flier_image] + [img.path for img in offer.images]:
        delete_old_image(path, current_app.config["UPLOAD_FOLDER"])
    db.session.delete(offer)
    db.session.commit()
    flash("Offer deleted.", "info")
    return redirect(url_for("admin.offer_list"))
