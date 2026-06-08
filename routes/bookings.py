"""Booking routes for tour package reservations."""
import os
from typing import Union
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload

from app import db
from models.booking import Booking
from models.package import TourPackage
from models.inquiry import Inquiry
from constants import BookingStatus, InquiryStatus
from forms import BookingForm, InquiryForm

bookings_bp = Blueprint('bookings', __name__)


@bookings_bp.route('/book/<int:package_id>', methods=['GET', 'POST'])
@login_required
def book_package(package_id: int) -> Union[str, object]:
    """Book a tour package with validation and error handling.
    
    Args:
        package_id: ID of the package to book
        
    Returns:
        Rendered template or redirect response
    """
    try:
        package = db.get_or_404(TourPackage, package_id)
    except Exception as e:
        current_app.logger.error(f"Error loading package {package_id}: {e}", exc_info=True)
        flash('Package not found.', 'danger')
        return redirect(url_for('packages.list_packages'))

    if not package.is_active:
        flash('This package is no longer available.', 'warning')
        return redirect(url_for('packages.list_packages'))

    form = BookingForm()
    if form.validate_on_submit():
        travel_date: date = form.travel_date.data
        
        # Validate travel date is in the future
        if travel_date < date.today():
            flash('Travel date must be in the future.', 'danger')
            return redirect(url_for('bookings.book_package', package_id=package_id))

        total_price: float = package.price * form.num_travelers.data

        try:
            # Attempt to reserve slots (atomic operation with row-level lock)
            updated = db.session.execute(
                update(TourPackage)
                .where(
                    TourPackage.id == package_id,
                    TourPackage.available_slots >= form.num_travelers.data
                )
                .values(available_slots=TourPackage.available_slots - form.num_travelers.data)
            )
            db.session.flush()

            if updated.rowcount == 0:
                current_app.logger.info(f"Insufficient slots for booking: package_id={package_id}, requested={form.num_travelers.data}")
                flash('Not enough slots available. Please try a smaller group size.', 'danger')
                return redirect(url_for('bookings.book_package', package_id=package_id))

            # Create booking record
            booking = Booking(
                user_id=current_user.id,
                package_id=package.id,
                contact_number=form.contact_number.data,
                num_travelers=form.num_travelers.data,
                travel_date=travel_date,
                end_travel_date=form.end_travel_date.data,
                total_price=total_price,
                special_requests=form.special_requests.data,
                status=BookingStatus.PENDING.value
            )

            db.session.add(booking)
            db.session.commit()
            current_app.logger.info(f"Booking created: id={booking.id}, user={current_user.id}, package={package_id}")

            # Send confirmation emails (with error handling)
            try:
                from email_service import send_booking_confirmation, send_admin_new_booking
                send_booking_confirmation(current_user, booking, package)
                admin_email = current_app.config.get('ADMIN_EMAIL', '')
                if admin_email:
                    send_admin_new_booking(admin_email, current_user, booking, package)
            except Exception as e:
                current_app.logger.warning(f"Email notification failed for booking #{booking.id}: {e}", exc_info=True)

            flash('Booking submitted successfully! We will confirm shortly.', 'success')
            return redirect(url_for('bookings.my_bookings'))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error creating booking: {e}", exc_info=True)
            flash('A booking error occurred. Please try again.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating booking: {e}", exc_info=True)
            flash('Database error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error creating booking for user {current_user.id}: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again later.', 'danger')

    return render_template('bookings/book.html', package=package, form=form)


@bookings_bp.route('/my-bookings')
@login_required
def my_bookings():
    """Display user's booking history with error handling and query optimization."""
    try:
        page = request.args.get('page', 1, type=int)
        # Use eager loading to prevent N+1 queries when accessing booking.package in template
        bookings = (
            Booking.query
            .filter_by(user_id=current_user.id)
            .options(joinedload(Booking.package))
            .order_by(Booking.created_at.desc())
            .paginate(page=page, per_page=10, error_out=False)
        )
        return render_template('bookings/my_bookings.html', bookings=bookings.items, pagination=bookings)
    except Exception as e:
        current_app.logger.error(f"Error loading bookings for user {current_user.id}: {e}", exc_info=True)
        flash('Could not load your bookings. Please try again.', 'danger')
        return redirect(url_for('main.home'))


@bookings_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel a booking with error handling."""
    try:
        booking = db.get_or_404(Booking, booking_id)
    except Exception as e:
        current_app.logger.error(f"Error loading booking {booking_id}: {e}", exc_info=True)
        flash('Booking not found.', 'danger')
        return redirect(url_for('bookings.my_bookings'))

    if booking.user_id != current_user.id:
        current_app.logger.warning(f"Unauthorized cancel attempt: user={current_user.id}, booking_id={booking_id}")
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('bookings.my_bookings'))

    if booking.status == BookingStatus.CANCELLED.value:
        flash('Booking already cancelled.', 'warning')
        return redirect(url_for('bookings.my_bookings'))

    try:
        booking.status = BookingStatus.CANCELLED.value

        # Atomic slot restoration to prevent race condition
        if booking.travel_date >= date.today():
            db.session.execute(
                update(TourPackage)
                .where(TourPackage.id == booking.package_id)
                .values(available_slots=TourPackage.available_slots + booking.num_travelers)
            )

        db.session.commit()
        current_app.logger.info(f"Booking cancelled: id={booking_id}, user={current_user.id}")
        flash('Booking cancelled successfully.', 'info')
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Database integrity error cancelling booking {booking_id}: {e}", exc_info=True)
        flash('An error occurred while cancelling. Please try again.', 'danger')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error cancelling booking {booking_id}: {e}", exc_info=True)
        flash('Database error occurred. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error cancelling booking {booking_id}: {e}", exc_info=True)
        flash('An unexpected error occurred. Please try again.', 'danger')

    return redirect(url_for('bookings.my_bookings'))


@bookings_bp.route('/plan-my-trip', methods=['GET', 'POST'])
def plan_my_trip():
    """Handle custom trip planning inquiries with comprehensive error handling."""
    if request.method == 'POST':
        try:
            name               = request.form.get('name', '').strip()
            email              = request.form.get('email', '').strip()
            contact_number     = request.form.get('contact_number', '').strip()
            destination        = request.form.get('destination', '').strip()
            travel_date_from_s = request.form.get('travel_date_from', '').strip()
            travel_date_to_s   = request.form.get('travel_date_to', '').strip()

            if not all([name, email, contact_number, destination]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('bookings.plan_my_trip'))

            try:
                num_adults   = max(1, int(request.form.get('num_adults', 1)))
                num_children = max(0, int(request.form.get('num_children', 0)))
                num_infants  = max(0, int(request.form.get('num_infants', 0)))
            except (ValueError, TypeError):
                flash('Please enter valid numbers for travelers.', 'danger')
                return redirect(url_for('bookings.plan_my_trip'))

            try:
                travel_date_from = datetime.strptime(travel_date_from_s, '%Y-%m-%d').date()
                travel_date_to   = datetime.strptime(travel_date_to_s, '%Y-%m-%d').date()
                
                if travel_date_from > travel_date_to:
                    flash('Start date must be before end date.', 'danger')
                    return redirect(url_for('bookings.plan_my_trip'))
                    
                if travel_date_from < date.today():
                    flash('Travel dates must be in the future.', 'danger')
                    return redirect(url_for('bookings.plan_my_trip'))
            except (ValueError, TypeError):
                flash('Invalid travel dates.', 'danger')
                return redirect(url_for('bookings.plan_my_trip'))

            special_requests = request.form.get('special_requests', '').strip()

            inquiry = Inquiry(
                name=name,
                email=email,
                contact_number=contact_number,
                destination=destination,
                travel_date_from=travel_date_from,
                travel_date_to=travel_date_to,
                num_adults=num_adults,
                num_children=num_children,
                num_infants=num_infants,
                special_requests=special_requests,
                status=InquiryStatus.NEW.value
            )
            db.session.add(inquiry)
            db.session.commit()
            current_app.logger.info(f"New inquiry created: id={inquiry.id}, from={email}, destination={destination}")

            # Send email notifications
            try:
                from email_service import send_admin_new_inquiry, send_inquiry_receipt
                
                # Send receipt to customer immediately
                send_inquiry_receipt(inquiry)
                
                # Alert admin
                admin_email = os.getenv('ADMIN_EMAIL', '')
                if admin_email:
                    send_admin_new_inquiry(admin_email, inquiry)
            except Exception as e:
                current_app.logger.warning(f"Email notification failed for inquiry #{inquiry.id}: {e}", exc_info=True)

            flash(f"Your trip inquiry has been submitted! Reference: {inquiry.reference_number} — Check your email for details.", 'success')
            return redirect(url_for('bookings.plan_my_trip'))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error creating inquiry: {e}", exc_info=True)
            flash('An error occurred. Please try again.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating inquiry: {e}", exc_info=True)
            flash('Database error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in plan_my_trip: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')

    return render_template('bookings/plan_my_trip.html')


@bookings_bp.route('/inquire/<int:package_id>', methods=['GET', 'POST'])
def inquire_package(package_id):
    """Inquiry form for a specific package - pre-fills destination with error handling."""
    try:
        package = db.get_or_404(TourPackage, package_id)
    except Exception as e:
        current_app.logger.error(f"Error loading package {package_id}: {e}", exc_info=True)
        flash('Package not found.', 'danger')
        return redirect(url_for('packages.list_packages'))

    if request.method == 'POST':
        try:
            name               = request.form.get('name', '').strip()
            email              = request.form.get('email', '').strip()
            contact_number     = request.form.get('contact_number', '').strip()
            destination        = request.form.get('destination', '').strip()
            travel_date_from_s = request.form.get('travel_date_from', '').strip()
            travel_date_to_s   = request.form.get('travel_date_to', '').strip()

            if not all([name, email, contact_number, destination]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('bookings.inquire_package', package_id=package_id))

            try:
                num_adults   = max(1, int(request.form.get('num_adults', 1)))
                num_children = max(0, int(request.form.get('num_children', 0)))
                num_infants  = max(0, int(request.form.get('num_infants', 0)))
            except (ValueError, TypeError):
                flash('Please enter valid numbers for travelers.', 'danger')
                return redirect(url_for('bookings.inquire_package', package_id=package_id))

            try:
                travel_date_from = datetime.strptime(travel_date_from_s, '%Y-%m-%d').date()
                travel_date_to   = datetime.strptime(travel_date_to_s, '%Y-%m-%d').date()
                
                if travel_date_from > travel_date_to:
                    flash('Start date must be before end date.', 'danger')
                    return redirect(url_for('bookings.inquire_package', package_id=package_id))
                    
                if travel_date_from < date.today():
                    flash('Travel dates must be in the future.', 'danger')
                    return redirect(url_for('bookings.inquire_package', package_id=package_id))
            except (ValueError, TypeError):
                flash('Invalid travel dates.', 'danger')
                return redirect(url_for('bookings.inquire_package', package_id=package_id))

            special_requests = request.form.get('special_requests', '').strip()

            inquiry = Inquiry(
                package_id=package_id,
                name=name,
                email=email,
                contact_number=contact_number,
                destination=destination,
                travel_date_from=travel_date_from,
                travel_date_to=travel_date_to,
                num_adults=num_adults,
                num_children=num_children,
                num_infants=num_infants,
                special_requests=special_requests,
                status=InquiryStatus.NEW.value
            )
            db.session.add(inquiry)
            db.session.commit()
            current_app.logger.info(f"New inquiry created for package {package_id}: id={inquiry.id}, from={email}")

            # Send email notifications
            try:
                from email_service import send_admin_new_inquiry, send_inquiry_receipt
                
                # Send receipt to customer immediately
                send_inquiry_receipt(inquiry)
                
                # Alert admin
                admin_email = os.getenv('ADMIN_EMAIL', '')
                if admin_email:
                    send_admin_new_inquiry(admin_email, inquiry)
            except Exception as e:
                current_app.logger.warning(f"Email notification failed for inquiry #{inquiry.id}: {e}", exc_info=True)

            flash(f"Your inquiry has been submitted! Reference: {inquiry.reference_number} — Check your email for details.", 'success')
            return redirect(url_for('bookings.inquire_package', package_id=package_id))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error creating inquiry: {e}", exc_info=True)
            flash('An error occurred. Please try again.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating inquiry: {e}", exc_info=True)
            flash('Database error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in inquire_package: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')

    return render_template('bookings/inquire_package.html', package=package)


@bookings_bp.route('/inquiry/<reference_number>')
def inquiry_status(reference_number):
    """Public inquiry status tracker - no login required.
    
    Allows customers to check their inquiry status using the reference number
    sent in the confirmation email.
    """
    try:
        inquiry = Inquiry.query.filter_by(reference_number=reference_number).first_or_404()
        
        # Build status timeline
        timeline = [
            {
                'status': 'Received',
                'label': 'Your inquiry received',
                'time': inquiry.created_at,
                'completed': True,
                'icon': '📧'
            },
            {
                'status': 'In Review',
                'label': 'Our team is reviewing your request',
                'time': None,
                'completed': inquiry.status in ['contacted', 'closed'],
                'icon': '👀'
            },
            {
                'status': 'Response Sent',
                'label': 'Personalized recommendations sent',
                'time': inquiry.responded_at if inquiry.status in ['contacted', 'closed'] else None,
                'completed': inquiry.status in ['contacted', 'closed'],
                'icon': '✅'
            }
        ]
        
        current_app.logger.info(f"Inquiry status viewed: {reference_number}")
        
        return render_template('bookings/inquiry_status.html', 
                             inquiry=inquiry, 
                             timeline=timeline)
    except Exception as e:
        current_app.logger.error(f"Error retrieving inquiry {reference_number}: {e}", exc_info=True)
        flash('Inquiry not found. Please check your reference number.', 'danger')
        return redirect(url_for('main.home'))
