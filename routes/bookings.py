"""Public inquiry routes — Plan My Trip, package inquiries, and inquiry status tracking.

Note: this module keeps the 'bookings' blueprint name/url_prefix for backward
compatibility with existing URLs (/bookings/plan-my-trip, /bookings/inquire/<id>,
/bookings/inquiry/<ref>). The old tour-booking flow (book_package, my_bookings,
cancel_booking) was removed since it was never reachable from the live site —
every customer-facing path (Plan My Trip, package inquiries, visa requests)
creates an Inquiry, not a Booking.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app import db, limiter
from models.package import TourPackage
from models.inquiry import Inquiry
from constants import InquiryStatus
from forms import InquiryForm
from flask_login import current_user
bookings_bp = Blueprint('bookings', __name__)


@bookings_bp.route('/plan-my-trip', methods=['GET', 'POST'])
@limiter.limit("10 per hour", methods=["POST"])
def plan_my_trip():
    form = InquiryForm()
    if form.validate_on_submit():
        try:
            inquiry = Inquiry(
                name=form.name.data,
                email=form.email.data.lower(),
                contact_number=form.contact_number.data,
                destination=form.destination.data,
                travel_date_from=form.travel_date_from.data,
                travel_date_to=form.travel_date_to.data,
                num_adults=form.num_adults.data,
                num_children=form.num_children.data or 0,
                num_infants=form.num_infants.data or 0,
                special_requests=form.special_requests.data,
                status=InquiryStatus.NEW.value,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(inquiry)
            db.session.commit()
            current_app.logger.info(
                f"New inquiry created: id={inquiry.id}, from={inquiry.email}, "
                f"destination={inquiry.destination}"
            )

            try:
                from notification_service import notify_inquiry_created, notify_admins_new_inquiry
                notify_inquiry_created(inquiry)
                notify_admins_new_inquiry(inquiry)
                db.session.commit()
            except Exception as notif_err:
                db.session.rollback()
                current_app.logger.warning(
                    f"In-app notification failed for inquiry #{inquiry.id}: {notif_err}", exc_info=True
                )

            from email_service import send_inquiry_emails_async
            base_url = current_app.config.get('SITE_URL') or request.host_url
            send_inquiry_emails_async(inquiry.id, base_url)

            return redirect(url_for('main.track_inquiry', reference_number=inquiry.reference_number))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"DB integrity error creating inquiry: {e}", exc_info=True)
            flash('An error occurred. Please try again.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"DB error creating inquiry: {e}", exc_info=True)
            flash('Database error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in plan_my_trip: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')

    return render_template('bookings/plan_my_trip.html', form=form)


@bookings_bp.route('/inquire/<int:package_id>', methods=['GET', 'POST'])
@limiter.limit("10 per hour", methods=["POST"])
def inquire_package(package_id):
    package = TourPackage.query.filter_by(id=package_id, is_active=True).first_or_404()

    form = InquiryForm()
    if form.validate_on_submit():
        try:
            inquiry = Inquiry(
                name=form.name.data,
                email=form.email.data.lower(),
                contact_number=form.contact_number.data,
                destination=form.destination.data,
                travel_date_from=form.travel_date_from.data,
                travel_date_to=form.travel_date_to.data,
                num_adults=form.num_adults.data,
                num_children=form.num_children.data or 0,
                num_infants=form.num_infants.data or 0,
                special_requests=form.special_requests.data,
                package_id=package_id,
                status=InquiryStatus.NEW.value,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(inquiry)
            db.session.commit()
            current_app.logger.info(
                f"New inquiry for package {package_id}: id={inquiry.id}, from={inquiry.email}"
            )

            try:
                from notification_service import notify_inquiry_created, notify_admins_new_inquiry
                notify_inquiry_created(inquiry)
                notify_admins_new_inquiry(inquiry)
                db.session.commit()
            except Exception as notif_err:
                db.session.rollback()
                current_app.logger.warning(
                    f"In-app notification failed for inquiry #{inquiry.id}: {notif_err}", exc_info=True
                )

            from email_service import send_inquiry_emails_async
            base_url = current_app.config.get('SITE_URL') or request.host_url
            send_inquiry_emails_async(inquiry.id, base_url)

            return redirect(url_for('main.track_inquiry', reference_number=inquiry.reference_number))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"DB integrity error creating inquiry: {e}", exc_info=True)
            flash('An error occurred. Please try again.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"DB error creating inquiry: {e}", exc_info=True)
            flash('Database error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in inquire_package: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')

    return render_template('bookings/inquire_package.html', package=package, form=form)


@bookings_bp.route('/inquiry/<reference_number>')
def inquiry_status(reference_number):
    """Deprecated — kept only so links from inquiry emails sent before this
    page was consolidated into main.track_inquiry still work."""
    return redirect(url_for('main.track_inquiry', reference_number=reference_number))