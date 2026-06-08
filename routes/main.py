"""Main routes for public pages and contact functionality."""
from typing import Union
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
import bleach

from app import db, limiter
from models.testimonial import Testimonial
from models.package import TourPackage
from models.contact import ContactMessage
from image_service import ImageUploadService, ImageUploadException
from utils import save_image_metadata, delete_old_image
from forms import ContactForm

main_bp = Blueprint('main', __name__)

ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']


@main_bp.route('/')
def home():
    """Home page with featured packages."""
    packages = TourPackage.query.filter_by(is_active=True).limit(3).all()
    return render_template('main/home.html', packages=packages)


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('main/about.html')


@main_bp.route('/reviews')
def reviews():
    """Reviews/testimonials page with pagination."""
    page = request.args.get('page', 1, type=int)
    pagination = (
        Testimonial.query
        .order_by(Testimonial.created_at.desc())
        .paginate(page=page, per_page=12, error_out=False)
    )
    return render_template('main/reviews.html', testimonials=pagination.items, pagination=pagination)


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page with email notifications."""
    form = ContactForm()
    if form.validate_on_submit():
        try:
            contact_msg = ContactMessage(
                name=form.name.data,
                email=form.email.data,
                subject=form.subject.data,
                message=form.message.data,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(contact_msg)
            db.session.commit()

            try:
                from email_service import send_contact_autoreply, send_contact_admin_alert
                send_contact_autoreply(form.name.data, form.email.data, form.subject.data)
                admin_email = current_app.config.get('ADMIN_EMAIL', '')
                if admin_email:
                    send_contact_admin_alert(
                        admin_email, form.name.data, form.email.data,
                        form.subject.data, form.message.data
                    )
            except Exception as e:
                current_app.logger.warning(f"Email notification failed for contact message: {e}")

            flash('Message sent! We will get back to you soon.', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Contact message creation failed: {e}", exc_info=True)
            flash(f'Error sending message: {str(e)}', 'danger')

    return render_template('main/contact.html', form=form)


@main_bp.route('/testimonial', methods=['POST'])
@login_required
@limiter.limit("5 uploads per hour")
def add_testimonial():
    """Add a testimonial with optional image uploads."""
    message = bleach.clean(request.form.get('message', '').strip(), tags=ALLOWED_TAGS, strip=True)
    try:
        rating = max(1, min(5, int(request.form.get('rating', 5))))
    except (ValueError, TypeError):
        rating = 5

    if not message:
        return jsonify(success=False, error='Message is required.'), 400

    image_files: list = request.files.getlist('image')
    image_filenames: list = []
    upload_results: list = []

    try:
        for image_file in image_files:
            if image_file and image_file.filename:
                try:
                    upload_result = ImageUploadService.upload_and_compress(image_file, 'review')
                    image_filenames.append(upload_result['path'])
                    upload_results.append(upload_result)
                except ImageUploadException as e:
                    return jsonify(success=False, error=str(e)), 400

        # FIX: model column is `image` (singular), not `images`
        image_column = ','.join(image_filenames) if image_filenames else None

        testimonial = Testimonial(
            user_id=current_user.id,
            message=message,
            rating=rating,
            image=image_column  # FIX: was `images=` which does not exist on the model
        )
        db.session.add(testimonial)

        # Persist image metadata (size + upload time) if an image was uploaded
        if upload_results:
            save_image_metadata(testimonial, upload_results[0], field_prefix='image')

        db.session.commit()

        image_urls = ['/uploads/' + f for f in image_filenames]

        return jsonify(
            success=True,
            id=testimonial.id,
            message=testimonial.message,
            rating=testimonial.rating,
            user_name=current_user.name,
            created_at=testimonial.created_at.strftime('%B %d, %Y'),
            delete_url=url_for('main.delete_testimonial', testimonial_id=testimonial.id),
            is_admin=current_user.is_admin,
            image_urls=image_urls
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Testimonial creation failed: {e}", exc_info=True)
        return jsonify(success=False, error='Failed to add testimonial'), 500


@main_bp.route('/testimonial/delete/<int:testimonial_id>', methods=['POST'])
@login_required
def delete_testimonial(testimonial_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    testimonial = db.get_or_404(Testimonial, testimonial_id)

    # Delete associated image files from disk
    if testimonial.image:
        for img_path in testimonial.image.split(','):
            delete_old_image(img_path.strip(), current_app.config['UPLOAD_FOLDER'])

    db.session.delete(testimonial)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True)
    flash('Review deleted.', 'success')
    return redirect(url_for('main.reviews'))
