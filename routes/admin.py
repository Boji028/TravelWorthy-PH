"""Admin panel routes for site management and content control."""
from typing import Union, Dict, Any, Optional
import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import bleach
from sqlalchemy.orm import joinedload

from app import db, limiter
from decorators import admin_required
from utils import delete_old_image, compress_image, save_image_metadata
from models.user import User
from models.package import TourPackage
from models.booking import Booking
from models.inquiry import Inquiry
from models.blog import BlogPost
from constants import BookingStatus, InquiryStatus
from image_service import ImageUploadService, ImageUploadException
from models.continent import Continent
from models.country import Country
from models.visa import VisaCountry
from models.contact import ContactMessage
from models.testimonial import Testimonial

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Fix 16: Explicit tag + attribute allowlist — blocks javascript: hrefs
ALLOWED_BLOG_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'h2', 'h3', 'a', 'blockquote']
ALLOWED_BLOG_ATTRS = {'a': ['href', 'title']}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file, prefix: str = 'img') -> Optional[str]:
    """Validate, save and compress an uploaded image. Returns filename or None.
    
    Deprecated: Use ImageUploadService.upload_and_compress() instead.
    
    Args:
        file: FileStorage object
        prefix: Prefix for filename
        
    Returns:
        Image path or None on error
    """
    try:
        result = ImageUploadService.upload_and_compress(file, prefix)
        return result['path'] if isinstance(result, dict) else result
    except ImageUploadException:
        return None


def get_dashboard_stats():
    """Get dashboard statistics with optimized queries.

    Returns:
        Dictionary with dashboard metrics
    """
    try:
        total_users      = User.query.filter_by(is_admin=False).count()
        total_packages   = TourPackage.query.count()
        total_bookings   = Booking.query.count()
        pending_bookings = Booking.query.filter_by(status=BookingStatus.PENDING.value).count()
        new_inquiries    = Inquiry.query.filter_by(status=InquiryStatus.NEW.value).count()

        # FIX: joinedload prevents N+1 queries when the template accesses booking.package.title
        recent_bookings = (
            Booking.query
            .options(joinedload(Booking.package))
            .order_by(Booking.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            'total_users':      total_users,
            'total_packages':   total_packages,
            'total_bookings':   total_bookings,
            'pending_bookings': pending_bookings,
            'new_inquiries':    new_inquiries,
            'recent_bookings':  recent_bookings,
        }
    except Exception as e:
        current_app.logger.error(f"Dashboard stats error: {e}", exc_info=True)
        return {
            'total_users':      0,
            'total_packages':   0,
            'total_bookings':   0,
            'pending_bookings': 0,
            'new_inquiries':    0,
            'recent_bookings':  [],
        }



# ── Dashboard ──────────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def dashboard() -> str:
    """Admin dashboard with site statistics."""
    stats = get_dashboard_stats()
    return render_template('admin/dashboard.html', **stats)


@admin_bp.route('/countries-by-continent/<int:continent_id>')
@admin_required
def countries_by_continent(continent_id):
    countries = Country.query.filter_by(continent_id=continent_id, is_active=True).order_by(Country.name).all()
    return jsonify([{'id': c.id, 'name': c.name, 'flag_emoji': c.flag_emoji} for c in countries])


# ── Packages ───────────────────────────────────────────────
@admin_bp.route('/packages')
@admin_required
def packages():
    page = request.args.get('page', 1, type=int)
    all_packages = TourPackage.query.order_by(TourPackage.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/packages.html', packages=all_packages.items, pagination=all_packages)


@admin_bp.route('/packages/add', methods=['GET', 'POST'])
@admin_required
@limiter.limit("10 uploads per hour")
def add_package():
    """Add new tour package with comprehensive error handling."""
    if request.method == 'POST':
        try:
            title       = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            destination = request.form.get('destination', '').strip()
            currency    = request.form.get('currency', 'PHP')

            if not all([title, description, destination]):
                flash('Please fill in all required fields.', 'danger')
                continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
                return render_template('admin/add_package.html', continents=continents)

            # Wrap all numeric casts in try/except
            try:
                country_id    = int(request.form.get('country_id')) if request.form.get('country_id') else None
                duration_days = int(request.form.get('duration_days', 1))
                price         = float(request.form.get('price', 0))
                max_slots     = int(request.form.get('max_slots', 20))
                
                if duration_days <= 0 or price < 0 or max_slots <= 0:
                    flash('Duration, price, and slots must be positive values.', 'danger')
                    continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
                    return render_template('admin/add_package.html', continents=continents)
            except (ValueError, TypeError):
                flash('Invalid numeric values. Please check duration, price, and slots.', 'danger')
                continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
                return render_template('admin/add_package.html', continents=continents)

            filename = 'default_tour.jpg'
            upload_result = None
            try:
                image_file = request.files.get('image')
                if image_file and image_file.filename:
                    upload_result = ImageUploadService.upload_and_compress(image_file, 'package')
                    filename = upload_result['path']
            except ImageUploadException as e:
                current_app.logger.warning(f"Package image upload failed: {e}")
                flash(f'Image upload failed: {str(e)}. Using default image.', 'warning')
            except Exception as e:
                current_app.logger.error(f"Unexpected error uploading package image: {e}", exc_info=True)
                flash('Image upload error. Using default image.', 'warning')

            package = TourPackage(
                title=title, description=description, destination=destination,
                country_id=country_id, duration_days=duration_days, price=price,
                currency=currency, max_slots=max_slots, available_slots=max_slots,
                image=filename,
                inclusions=request.form.get('inclusions', '').strip(),
                exclusions=request.form.get('exclusions', '').strip(),
            )
            db.session.add(package)
            db.session.commit()
            
            if upload_result:
                try:
                    save_image_metadata(package, upload_result, field_prefix='image')
                    db.session.commit()
                except Exception as e:
                    current_app.logger.warning(f"Could not save image metadata for package {package.id}: {e}")

            current_app.logger.info(f"Package added by admin: id={package.id}, title={title}")
            flash('Tour package added successfully!', 'success')
            return redirect(url_for('admin.packages'))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error adding package: {e}", exc_info=True)
            flash('A package with this title may already exist. Please try another.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error adding package: {e}", exc_info=True)
            flash('Database error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error adding package: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')

        continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
        return render_template('admin/add_package.html', continents=continents)

    continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
    return render_template('admin/add_package.html', continents=continents)


@admin_bp.route('/packages/edit/<int:package_id>', methods=['GET', 'POST'])
@admin_required
def edit_package(package_id):
    """Edit tour package with comprehensive error handling."""
    try:
        package = db.get_or_404(TourPackage, package_id)
    except Exception as e:
        current_app.logger.error(f"Error loading package {package_id}: {e}", exc_info=True)
        flash('Package not found.', 'danger')
        return redirect(url_for('admin.packages'))

    if request.method == 'POST':
        try:
            package.title       = request.form.get('title', '').strip()
            package.description = request.form.get('description', '').strip()
            package.destination = request.form.get('destination', '').strip()
            package.is_active   = bool(request.form.get('is_active'))
            package.inclusions  = request.form.get('inclusions', '').strip()
            package.exclusions  = request.form.get('exclusions', '').strip()
            package.currency    = request.form.get('currency', 'PHP')

            if not all([package.title, package.description, package.destination]):
                flash('Please fill in all required fields.', 'danger')
                continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
                return render_template('admin/edit_package.html', package=package, continents=continents)

            # Wrap numeric casts
            try:
                package.duration_days = int(request.form.get('duration_days', 1))
                package.price         = float(request.form.get('price', 0))
                package.country_id    = int(request.form.get('country_id')) if request.form.get('country_id') else None
                new_max_slots         = int(request.form.get('max_slots', package.max_slots))
                
                if package.duration_days <= 0 or package.price < 0 or new_max_slots <= 0:
                    flash('Duration, price, and slots must be positive values.', 'danger')
                    continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
                    return render_template('admin/edit_package.html', package=package, continents=continents)
            except (ValueError, TypeError):
                flash('Invalid numeric values. Please check duration, price, and slots.', 'danger')
                continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
                return render_template('admin/edit_package.html', package=package, continents=continents)

            if new_max_slots != package.max_slots:
                try:
                    booked = db.session.query(func.sum(Booking.num_travelers)).filter(
                        Booking.package_id == package.id,
                        Booking.status.in_([BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value])
                    ).scalar() or 0
                    package.max_slots       = new_max_slots
                    package.available_slots = max(0, new_max_slots - booked)
                except Exception as e:
                    current_app.logger.error(f"Error calculating available slots: {e}", exc_info=True)
                    flash('Error calculating slots. Please try again.', 'danger')
                    continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
                    return render_template('admin/edit_package.html', package=package, continents=continents)
            else:
                package.max_slots = new_max_slots

            try:
                image_file = request.files.get('image')
                if image_file and image_file.filename:
                    upload_result = ImageUploadService.upload_and_compress(image_file, 'package')
                    delete_old_image(package.image, current_app.config['UPLOAD_FOLDER'])
                    package.image = upload_result['path']
                    save_image_metadata(package, upload_result, field_prefix='image')
            except ImageUploadException as e:
                current_app.logger.warning(f"Package image update failed: {e}")
                flash(f'Image upload failed: {str(e)}', 'warning')
            except Exception as e:
                current_app.logger.error(f"Unexpected error updating package image: {e}", exc_info=True)
                flash('Image update error occurred.', 'warning')

            db.session.commit()
            current_app.logger.info(f"Package updated by admin: id={package_id}, title={package.title}")
            flash('Package updated successfully!', 'success')
            return redirect(url_for('admin.packages'))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error updating package {package_id}: {e}", exc_info=True)
            flash('Database integrity error. Please try again.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating package {package_id}: {e}", exc_info=True)
            flash('Database error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error updating package {package_id}: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')

    continents = Continent.query.filter_by(is_active=True).order_by(Continent.name).all()
    return render_template('admin/edit_package.html', package=package, continents=continents)


@admin_bp.route('/packages/delete/<int:package_id>', methods=['POST'])
@admin_required
def delete_package(package_id):
    package = db.get_or_404(TourPackage, package_id)
    delete_old_image(package.image, current_app.config['UPLOAD_FOLDER'])
    db.session.delete(package)
    db.session.commit()
    flash('Package deleted.', 'info')
    return redirect(url_for('admin.packages'))


# ── Bookings ───────────────────────────────────────────────
@admin_bp.route('/bookings')
@admin_required
def bookings():
    from sqlalchemy.orm import joinedload
    status_filter = request.args.get('status', '')
    # Fix 10: joinedload avoids N+1 queries when rendering package titles in the list
    query = Booking.query.options(joinedload(Booking.package))
    if status_filter:
        query = query.filter_by(status=status_filter)
    page = request.args.get('page', 1, type=int)
    all_bookings = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/bookings.html', bookings=all_bookings.items, pagination=all_bookings, status_filter=status_filter)


@admin_bp.route('/bookings/update/<int:booking_id>', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    user = booking.user
    package = booking.package
    new_status = request.form.get('status')
    old_status = booking.status
    valid_statuses = [status.value for status in BookingStatus]
    if new_status in valid_statuses:
        booking.status = new_status
        db.session.commit()
        
        # Send email notifications based on status change
        from email_service import send_booking_approved, send_booking_rejected, send_booking_cancellation
        
        if new_status == BookingStatus.CONFIRMED.value and old_status != BookingStatus.CONFIRMED.value:
            send_booking_approved(user, booking, package)
        elif new_status == BookingStatus.CANCELLED.value and old_status != BookingStatus.CANCELLED.value:
            send_booking_cancellation(user, booking, package)
        elif new_status == BookingStatus.REJECTED.value and old_status != BookingStatus.REJECTED.value:
            send_booking_rejected(user, booking, package)
        
        flash(f'Booking #{booking.id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.bookings'))


# ── Users ──────────────────────────────────────────────────
@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    all_users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=all_users.items, pagination=all_users)


# ── Inquiries ──────────────────────────────────────────────
@admin_bp.route('/inquiries')
@admin_required
def inquiries():
    status_filter = request.args.get('status', '')
    query = Inquiry.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    page = request.args.get('page', 1, type=int)
    all_inquiries = query.order_by(Inquiry.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/inquiries.html', inquiries=all_inquiries.items, pagination=all_inquiries, status_filter=status_filter)


@admin_bp.route('/inquiries/update/<int:inquiry_id>', methods=['POST'])
@admin_required
def update_inquiry_status(inquiry_id):
    inquiry = db.get_or_404(Inquiry, inquiry_id)
    new_status = request.form.get('status')
    if new_status in ['new', 'contacted', 'closed']:
        inquiry.status = new_status
        db.session.commit()
        flash(f'Inquiry #{inquiry.id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.inquiries'))


@admin_bp.route('/inquiries/reply/<int:inquiry_id>', methods=['POST'])
@admin_required
def reply_to_inquiry(inquiry_id):
    inquiry = db.get_or_404(Inquiry, inquiry_id)
    admin_response = request.form.get('response', '').strip()
    
    if not admin_response:
        flash('Please provide a response message.', 'danger')
        return redirect(url_for('admin.inquiries'))
    
    try:
        from email_service import send_inquiry_reply
        
        inquiry.admin_response = admin_response
        inquiry.responded_at = datetime.now(timezone.utc)
        inquiry.status = 'contacted'
        db.session.commit()
        
        # Send email to customer
        send_inquiry_reply(inquiry, admin_response)
        
        flash(f'Response sent to {inquiry.email}!', 'success')
    except Exception as e:
        flash(f'Error sending response: {str(e)}', 'danger')
    
    return redirect(url_for('admin.inquiries'))


@admin_bp.route('/inquiries/delete/<int:inquiry_id>', methods=['POST'])
@admin_required
def delete_inquiry(inquiry_id):
    inquiry = db.get_or_404(Inquiry, inquiry_id)
    db.session.delete(inquiry)
    db.session.commit()
    flash('Inquiry deleted.', 'info')
    return redirect(url_for('admin.inquiries'))


# ── Blog ──────────────────────────────────────────────────
@admin_bp.route('/blog')
@admin_required
def blog():
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/blog.html', posts=posts.items, pagination=posts)


@admin_bp.route('/blog/add', methods=['GET', 'POST'])
@admin_required
@limiter.limit("10 uploads per hour")
def add_blog():
    if request.method == 'POST':
        try:
            import sys
            print("=== ADD_BLOG DEBUG START ===", file=sys.stderr)
            print(f"Form keys: {list(request.form.keys())}", file=sys.stderr)
            print(f"Files keys: {list(request.files.keys())}", file=sys.stderr)
            
            title             = request.form.get('title', '').strip()
            author            = request.form.get('author', 'Admin').strip()
            category          = request.form.get('category', '').strip()
            short_description = request.form.get('short_description', '').strip()
            # Fix 16: Pass explicit attributes to block javascript: hrefs
            content = bleach.clean(
                request.form.get('content', '').strip(),
                tags=ALLOWED_BLOG_TAGS,
                attributes=ALLOWED_BLOG_ATTRS,
                strip=True
            )
            is_published = request.form.get('is_published') == 'on'
            print(f"Form parsed: title={title[:20]}..., has_content={bool(content)}", file=sys.stderr)

            if not title or not content:
                flash('Title and content are required.', 'danger')
                return redirect(url_for('admin.add_blog'))

            featured_image = None
            upload_result = None
            try:
                featured_file = request.files.get('featured_image')
                if featured_file and featured_file.filename:
                    print(f">>> Image upload starting: {featured_file.filename}", file=sys.stderr)
                    current_app.logger.info(f'Uploading file: {featured_file.filename}')
                    upload_result = ImageUploadService.upload_and_compress(featured_file, 'blog')
                    featured_image = upload_result['path']
                    print(f">>> Image upload successful: {featured_image}", file=sys.stderr)
                    current_app.logger.info(f'Upload successful: {featured_image}')
            except ImageUploadException as e:
                print(f"!!! ImageUploadException: {e}", file=sys.stderr)
                current_app.logger.error(f'ImageUploadException: {str(e)}')
                flash(f'Image upload failed: {str(e)}', 'danger')
                return redirect(url_for('admin.add_blog'))
            except Exception as e:
                print(f"!!! Image upload exception: {type(e).__name__}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                current_app.logger.error(f'Image upload error: {type(e).__name__}: {str(e)}', exc_info=True)
                flash(f'Image upload failed: {str(e)}', 'danger')
                return redirect(url_for('admin.add_blog'))

            post = BlogPost(
                title=title, author=author, category=category,
                short_description=short_description, content=content,
                featured_image=featured_image, is_published=is_published
            )
            print(f">>> Creating blog post object", file=sys.stderr)
            db.session.add(post)
            print(f">>> Adding to session", file=sys.stderr)
            db.session.commit()
            print(f">>> Committed to database", file=sys.stderr)
            current_app.logger.info(f'Blog post created: {post.id}')
            
            if upload_result:
                try:
                    print(f">>> Saving image metadata", file=sys.stderr)
                    save_image_metadata(post, upload_result, field_prefix='featured_image')
                    db.session.commit()
                    print(f">>> Metadata committed", file=sys.stderr)
                    current_app.logger.info(f'Image metadata saved for post {post.id}')
                except Exception as e:
                    print(f"!!! Error saving metadata: {type(e).__name__}: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    current_app.logger.error(f'Error saving image metadata: {type(e).__name__}: {str(e)}', exc_info=True)
                    # Don't fail the whole operation just because metadata save failed
            
            print(f">>> Success! Flashing success message", file=sys.stderr)
            flash('Blog post published!', 'success')
            print(f"=== ADD_BLOG DEBUG END ===", file=sys.stderr)
            return redirect(url_for('admin.blog'))
        
        except Exception as e:
            current_app.logger.error(f'Unexpected error in add_blog: {type(e).__name__}: {str(e)}', exc_info=True)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            return redirect(url_for('admin.add_blog'))

    return render_template('admin/add_blog.html')


@admin_bp.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
@limiter.limit("10 uploads per hour")
def edit_blog(post_id):
    post = db.get_or_404(BlogPost, post_id)
    if request.method == 'POST':
        post.title             = request.form.get('title', '').strip()
        post.author            = request.form.get('author', 'Admin').strip()
        post.category          = request.form.get('category', '').strip()
        post.short_description = request.form.get('short_description', '').strip()
        # Fix 16: Explicit attributes
        post.content = bleach.clean(
            request.form.get('content', '').strip(),
            tags=ALLOWED_BLOG_TAGS,
            attributes=ALLOWED_BLOG_ATTRS,
            strip=True
        )
        post.is_published = request.form.get('is_published') == 'on'

        try:
            featured_file = request.files.get('featured_image')
            if featured_file and featured_file.filename:
                upload_result = ImageUploadService.upload_and_compress(featured_file, 'blog')
                delete_old_image(post.featured_image, current_app.config['UPLOAD_FOLDER'])
                post.featured_image = upload_result['path']
                save_image_metadata(post, upload_result, field_prefix='featured_image')
                db.session.commit()
        except ImageUploadException as e:
            flash(f'Image upload failed: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_blog', post_id=post_id))

        db.session.commit()
        flash('Blog post updated!', 'success')
        return redirect(url_for('admin.blog'))
    return render_template('admin/edit_blog.html', post=post)


@admin_bp.route('/blog/delete/<int:post_id>', methods=['POST'])
@admin_required
def delete_blog(post_id):
    post = db.get_or_404(BlogPost, post_id)
    delete_old_image(post.featured_image, current_app.config['UPLOAD_FOLDER'])
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted.', 'info')
    return redirect(url_for('admin.blog'))


# ── Continents ────────────────────────────────────────────
@admin_bp.route('/continents')
@admin_required
def continents():
    all_continents = Continent.query.order_by(Continent.name).all()
    return render_template('admin/continents.html', continents=all_continents)


@admin_bp.route('/continents/add', methods=['GET', 'POST'])
@admin_required
def add_continent():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        flag_emoji  = request.form.get('flag_emoji', '').strip()
        description = request.form.get('description', '').strip()
        is_active   = request.form.get('is_active') == 'on'
        if not name:
            flash('Continent name is required.', 'danger')
            return redirect(url_for('admin.add_continent'))
        continent = Continent(name=name, flag_emoji=flag_emoji, description=description, is_active=is_active)
        db.session.add(continent)
        db.session.commit()
        flash(f'{name} added successfully!', 'success')
        return redirect(url_for('admin.continents'))
    return render_template('admin/add_continent.html')


@admin_bp.route('/continents/edit/<int:continent_id>', methods=['GET', 'POST'])
@admin_required
def edit_continent(continent_id):
    continent = db.get_or_404(Continent, continent_id)
    if request.method == 'POST':
        continent.name        = request.form.get('name', '').strip()
        continent.flag_emoji  = request.form.get('flag_emoji', '').strip()
        continent.description = request.form.get('description', '').strip()
        continent.is_active   = request.form.get('is_active') == 'on'
        db.session.commit()
        flash(f'{continent.name} updated!', 'success')
        return redirect(url_for('admin.continents'))
    return render_template('admin/edit_continent.html', continent=continent)


@admin_bp.route('/continents/delete/<int:continent_id>', methods=['POST'])
@admin_required
def delete_continent(continent_id):
    continent = db.get_or_404(Continent, continent_id)
    db.session.delete(continent)
    db.session.commit()
    flash('Continent deleted.', 'info')
    return redirect(url_for('admin.continents'))


# ── Countries ─────────────────────────────────────────────
@admin_bp.route('/countries')
@admin_required
def countries():
    continent_id  = request.args.get('continent_id', type=int)
    continent     = db.get_or_404(Continent, continent_id) if continent_id else None
    all_countries = Country.query.filter_by(continent_id=continent_id).order_by(Country.name).all() if continent_id else []
    return render_template('admin/countries.html', countries=all_countries, continent=continent)


@admin_bp.route('/countries/add', methods=['GET', 'POST'])
@admin_required
def add_country():
    continent_id = request.args.get('continent_id', type=int)
    continent    = db.get_or_404(Continent, continent_id) if continent_id else None
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        flag_emoji  = request.form.get('flag_emoji', '').strip()
        description = request.form.get('description', '').strip()
        is_active   = request.form.get('is_active') == 'on'
        if not name:
            flash('Country name is required.', 'danger')
            return redirect(url_for('admin.countries', continent_id=continent_id))

        image   = ''
        upload_result = None
        try:
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                upload_result = ImageUploadService.upload_and_compress(image_file, 'country')
                image = upload_result['path']
        except ImageUploadException as e:
            flash(f'Image upload failed: {str(e)}', 'danger')
            return redirect(url_for('admin.add_country', continent_id=continent_id))

        country = Country(name=name, flag_emoji=flag_emoji, description=description,
                          image=image, is_active=is_active, continent_id=continent_id)
        db.session.add(country)
        db.session.commit()
        if upload_result:
            save_image_metadata(country, upload_result, field_prefix='image')
            db.session.commit()
        flash(f'{name} added successfully!', 'success')
        return redirect(url_for('admin.countries', continent_id=continent_id))
    return render_template('admin/add_country.html', continent=continent)


@admin_bp.route('/countries/edit/<int:country_id>', methods=['GET', 'POST'])
@admin_required
def edit_country(country_id):
    country = db.get_or_404(Country, country_id)
    if request.method == 'POST':
        country.name        = request.form.get('name', '').strip()
        country.flag_emoji  = request.form.get('flag_emoji', '').strip()
        country.description = request.form.get('description', '').strip()
        country.is_active   = request.form.get('is_active') == 'on'

        try:
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                upload_result = ImageUploadService.upload_and_compress(image_file, 'country')
                delete_old_image(country.image, current_app.config['UPLOAD_FOLDER'])
                country.image = upload_result['path']
                save_image_metadata(country, upload_result, field_prefix='image')
                db.session.commit()
        except ImageUploadException as e:
            flash(f'Image upload failed: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_country', country_id=country_id))

        db.session.commit()
        flash(f'{country.name} updated!', 'success')
        return redirect(url_for('admin.countries', continent_id=country.continent_id))
    return render_template('admin/edit_country.html', country=country)


@admin_bp.route('/countries/delete/<int:country_id>', methods=['POST'])
@admin_required
def delete_country(country_id):
    country      = db.get_or_404(Country, country_id)
    continent_id = country.continent_id
    delete_old_image(country.image, current_app.config['UPLOAD_FOLDER'])
    db.session.delete(country)
    db.session.commit()
    flash('Country deleted.', 'info')
    return redirect(url_for('admin.countries', continent_id=continent_id))


# ── Contact Messages ──────────────────────────────────────
@admin_bp.route('/contact-messages')
@admin_required
def contact_messages():
    page     = request.args.get('page', 1, type=int)
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/contact_messages.html', messages=messages.items, pagination=messages)


@admin_bp.route('/contact-messages/mark-read/<int:message_id>', methods=['POST'])
@admin_required
def mark_message_read(message_id):
    msg = db.get_or_404(ContactMessage, message_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin.contact_messages'))


@admin_bp.route('/contact-messages/delete/<int:message_id>', methods=['POST'])
@admin_required
def delete_contact_message(message_id):
    msg = db.get_or_404(ContactMessage, message_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('admin.contact_messages'))


# ── Visa ──────────────────────────────────────────────────
@admin_bp.route('/visa')
@admin_required
def visa_list():
    visas = VisaCountry.query.order_by(VisaCountry.country_name).all()
    return render_template('admin/visa.html', visas=visas)


@admin_bp.route('/visa/add', methods=['GET', 'POST'])
@admin_required
@limiter.limit("10 uploads per hour")
def visa_add():
    if request.method == 'POST':
        country_name = request.form.get('country_name', '').strip()
        flag_emoji   = request.form.get('flag_emoji', '').strip()
        is_active    = request.form.get('is_active') == 'on'
        if not country_name:
            flash('Country name is required.', 'danger')
            return redirect(url_for('admin.visa_add'))

        pdf_filename = None
        pdf_file = request.files.get('requirements_pdf')
        if pdf_file and pdf_file.filename:
            if not pdf_file.filename.lower().endswith('.pdf'):
                flash('Only PDF files are allowed for requirements.', 'danger')
                return redirect(url_for('admin.visa_add'))
            try:
                # Validate PDF file size (max 5MB)
                pdf_file.seek(0, os.SEEK_END)
                pdf_size = pdf_file.tell()
                pdf_file.seek(0)
                if pdf_size > 5 * 1024 * 1024:
                    flash('PDF file too large. Maximum: 5MB', 'danger')
                    return redirect(url_for('admin.visa_add'))
                pdf_filename = secure_filename(pdf_file.filename)
                pdf_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_filename))
            except Exception as e:
                flash(f'PDF upload failed: {str(e)}', 'danger')
                return redirect(url_for('admin.visa_add'))

        image_filename = None
        upload_result = None
        try:
            image_file = request.files.get('country_image')
            if image_file and image_file.filename:
                upload_result = ImageUploadService.upload_and_compress(image_file, 'visa')
                image_filename = upload_result['path']
        except ImageUploadException as e:
            flash(f'Image upload failed: {str(e)}', 'danger')
            return redirect(url_for('admin.visa_add'))

        try:
            price = float(request.form.get('price')) if request.form.get('price') else None
        except ValueError:
            price = None

        visa = VisaCountry(country_name=country_name, flag_emoji=flag_emoji,
                           requirements_pdf=pdf_filename, country_image=image_filename,
                           price=price, is_active=is_active)
        db.session.add(visa)
        db.session.commit()
        if upload_result:
            save_image_metadata(visa, upload_result, field_prefix='country_image')
            db.session.commit()
        flash(f'{country_name} visa added!', 'success')
        return redirect(url_for('admin.visa_list'))
    return render_template('admin/add_visa.html')


@admin_bp.route('/visa/edit/<int:visa_id>', methods=['GET', 'POST'])
@admin_required
@limiter.limit("10 uploads per hour")
def visa_edit(visa_id):
    visa = db.get_or_404(VisaCountry, visa_id)
    if request.method == 'POST':
        visa.country_name = request.form.get('country_name', '').strip()
        visa.flag_emoji   = request.form.get('flag_emoji', '').strip()
        visa.is_active    = request.form.get('is_active') == 'on'

        pdf_file = request.files.get('requirements_pdf')
        if pdf_file and pdf_file.filename:
            if not pdf_file.filename.lower().endswith('.pdf'):
                flash('Only PDF files are allowed for requirements.', 'danger')
                return redirect(url_for('admin.visa_edit', visa_id=visa_id))
            try:
                # Validate PDF file size (max 5MB)
                pdf_file.seek(0, os.SEEK_END)
                pdf_size = pdf_file.tell()
                pdf_file.seek(0)
                if pdf_size > 5 * 1024 * 1024:
                    flash('PDF file too large. Maximum: 5MB', 'danger')
                    return redirect(url_for('admin.visa_edit', visa_id=visa_id))
                pdf_filename = secure_filename(pdf_file.filename)
                pdf_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_filename))
                visa.requirements_pdf = pdf_filename
            except Exception as e:
                flash(f'PDF upload failed: {str(e)}', 'danger')
                return redirect(url_for('admin.visa_edit', visa_id=visa_id))

        try:
            image_file = request.files.get('country_image')
            if image_file and image_file.filename:
                upload_result = ImageUploadService.upload_and_compress(image_file, 'visa')
                delete_old_image(visa.country_image, current_app.config['UPLOAD_FOLDER'])
                visa.country_image = upload_result['path']
                save_image_metadata(visa, upload_result, field_prefix='country_image')
                db.session.commit()
        except ImageUploadException as e:
            flash(f'Image upload failed: {str(e)}', 'danger')
            return redirect(url_for('admin.visa_edit', visa_id=visa_id))

        try:
            visa.price = float(request.form.get('price')) if request.form.get('price') else None
        except ValueError:
            visa.price = None

        db.session.commit()
        flash(f'{visa.country_name} updated!', 'success')
        return redirect(url_for('admin.visa_list'))
    return render_template('admin/edit_visa.html', visa=visa)


@admin_bp.route('/visa/delete/<int:visa_id>', methods=['POST'])
@admin_required
def visa_delete(visa_id):
    visa = db.get_or_404(VisaCountry, visa_id)
    delete_old_image(visa.country_image, current_app.config['UPLOAD_FOLDER'])
    db.session.delete(visa)
    db.session.commit()
    flash('Visa entry deleted.', 'info')
    return redirect(url_for('admin.visa_list'))


# ── Testimonials ──────────────────────────────────────────
@admin_bp.route('/testimonials')
@admin_required
def testimonials():
    page = request.args.get('page', 1, type=int)
    testimonials_data = Testimonial.query.order_by(Testimonial.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/testimonials.html', testimonials=testimonials_data.items, pagination=testimonials_data)


@admin_bp.route('/testimonials/delete-photo/<int:testimonial_id>', methods=['POST'])
@admin_required
def delete_testimonial_photo(testimonial_id):
    testimonial = db.get_or_404(Testimonial, testimonial_id)
    if testimonial.image:
        image_paths = testimonial.image.split(',')
        for img_path in image_paths:
            delete_old_image(img_path.strip(), current_app.config['UPLOAD_FOLDER'])
        testimonial.image = None
        db.session.commit()
        flash('Testimonial photo(s) removed.', 'success')
    return redirect(url_for('admin.testimonials'))


# ── Photo Removal Routes (for quick deletion) ──────────────
@admin_bp.route('/packages/remove-photo/<int:package_id>', methods=['POST'])
@admin_required
def remove_package_photo(package_id):
    """Remove photo from a package."""
    package = db.get_or_404(TourPackage, package_id)
    if package.image and package.image != 'default_tour.jpg':
        delete_old_image(package.image, current_app.config['UPLOAD_FOLDER'])
        package.image = None
        db.session.commit()
        flash('Package photo removed.', 'success')
    else:
        flash('No photo to remove.', 'warning')
    return redirect(url_for('admin.edit_package', package_id=package_id))


@admin_bp.route('/blog/remove-photo/<int:post_id>', methods=['POST'])
@admin_required
def remove_blog_photo(post_id):
    """Remove featured image from a blog post."""
    post = db.get_or_404(BlogPost, post_id)
    if post.featured_image:
        delete_old_image(post.featured_image, current_app.config['UPLOAD_FOLDER'])
        post.featured_image = None
        db.session.commit()
        flash('Blog photo removed.', 'success')
    else:
        flash('No photo to remove.', 'warning')
    return redirect(url_for('admin.edit_blog', post_id=post_id))


@admin_bp.route('/visa/remove-photo/<int:visa_id>', methods=['POST'])
@admin_required
def remove_visa_photo(visa_id):
    """Remove country image from a visa entry."""
    visa = db.get_or_404(VisaCountry, visa_id)
    if visa.country_image:
        delete_old_image(visa.country_image, current_app.config['UPLOAD_FOLDER'])
        visa.country_image = None
        db.session.commit()
        flash('Visa photo removed.', 'success')
    else:
        flash('No photo to remove.', 'warning')
    return redirect(url_for('admin.visa_edit', visa_id=visa_id))


@admin_bp.route('/visa/remove-pdf/<int:visa_id>', methods=['POST'])
@admin_required
def remove_visa_pdf(visa_id):
    """Remove requirements PDF from a visa entry."""
    visa = db.get_or_404(VisaCountry, visa_id)
    if visa.requirements_pdf:
        delete_old_image(visa.requirements_pdf, current_app.config['UPLOAD_FOLDER'])
        visa.requirements_pdf = None
        db.session.commit()
        flash('Visa PDF removed.', 'success')
    else:
        flash('No PDF to remove.', 'warning')
    return redirect(url_for('admin.visa_edit', visa_id=visa_id))
