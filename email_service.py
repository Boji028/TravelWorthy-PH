"""Centralised email sending helpers."""
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail


def _send(subject: str, recipients: list, body: str, html: str = None) -> None:
    """Send an email, silently failing if mail is not configured."""
    if not current_app.config.get('MAIL_USERNAME'):
        return  # Mail not configured — skip silently
    try:
        msg = Message(subject=subject, recipients=recipients, body=body, html=html)
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Email send error: {e}")


def send_booking_confirmation(user, booking, package) -> None:
    subject = f"Booking Confirmed — {package.title}"
    body = (
        f"Hi {user.name},\n\n"
        f"Your booking for '{package.title}' has been received!\n\n"
        f"  Travel date : {booking.travel_date.strftime('%B %d, %Y')}\n"
        f"  Travelers   : {booking.num_travelers}\n"
        f"  Total price : {package.currency} {booking.total_price:,.2f}\n"
        f"  Status      : Pending confirmation\n\n"
        "We will contact you shortly to confirm your booking.\n\n"
        "Thank you for choosing Travel Worthy PH!"
    )
    _send(subject, [user.email], body)


def send_admin_new_booking(admin_email: str, user, booking, package) -> None:
    subject = f"[Admin] New Booking #{booking.id} — {package.title}"
    body = (
        f"A new booking has been submitted.\n\n"
        f"  Booking ID  : #{booking.id}\n"
        f"  Customer    : {user.name} ({user.email})\n"
        f"  Package     : {package.title}\n"
        f"  Travel date : {booking.travel_date.strftime('%B %d, %Y')}\n"
        f"  Travelers   : {booking.num_travelers}\n"
        f"  Total       : {package.currency} {booking.total_price:,.2f}\n"
    )
    _send(subject, [admin_email], body)


def send_admin_new_inquiry(admin_email: str, inquiry) -> None:
    subject = f"[Admin] New Trip Inquiry from {inquiry.name}"
    package_info = ""
    if inquiry.package_id and inquiry.package:
        package_info = f"  Package     : {inquiry.package.title}\n"
    
    body = (
        f"New inquiry received.\n\n"
        f"  Name        : {inquiry.name}\n"
        f"  Email       : {inquiry.email}\n"
        f"  Contact     : {inquiry.contact_number}\n"
        f"  Destination : {inquiry.destination}\n"
        f"{package_info}"
        f"  Dates       : {inquiry.travel_date_from} → {inquiry.travel_date_to}\n"
        f"  Pax         : {inquiry.num_adults}A / {inquiry.num_children}C / {inquiry.num_infants}I\n"
        f"  Notes       : {inquiry.special_requests or '—'}\n"
    )
    _send(subject, [admin_email], body)


def send_contact_autoreply(name: str, to_email: str, subject: str) -> None:
    reply_subject = f"Re: {subject}"
    body = (
        f"Hi {name},\n\n"
        "Thank you for reaching out to Travel Worthy PH! "
        "We have received your message and will get back to you within 24 hours.\n\n"
        "Best regards,\nTravel Worthy PH Team"
    )
    _send(reply_subject, [to_email], body)


def send_contact_admin_alert(admin_email: str, name: str, email: str, subject: str, message: str) -> None:
    alert_subject = f"[Admin] New Contact Message: {subject}"
    body = (
        f"New contact form submission.\n\n"
        f"  From    : {name} ({email})\n"
        f"  Subject : {subject}\n\n"
        f"  Message :\n{message}\n"
    )
    _send(alert_subject, [admin_email], body)


def send_booking_approved(user, booking, package) -> None:
    """Send email when a booking is approved by admin."""
    subject = f"Booking Approved! — {package.title}"
    body = (
        f"Hi {user.name},\n\n"
        f"Great news! Your booking for '{package.title}' has been approved.\n\n"
        f"  Booking ID  : #{booking.id}\n"
        f"  Travel date : {booking.travel_date.strftime('%B %d, %Y')}\n"
        f"  Travelers   : {booking.num_travelers}\n"
        f"  Total price : {package.currency} {booking.total_price:,.2f}\n"
        f"  Status      : APPROVED\n\n"
        "Get ready for an amazing adventure! "
        "We'll contact you with further details closer to your travel date.\n\n"
        "Thank you for choosing Travel Worthy PH!"
    )
    _send(subject, [user.email], body)


def send_booking_rejected(user, booking, package, reason: str = "") -> None:
    """Send email when a booking is rejected by admin."""
    subject = f"Booking Status Update — {package.title}"
    body = (
        f"Hi {user.name},\n\n"
        f"We regret to inform you that your booking for '{package.title}' "
        f"could not be processed at this time.\n\n"
        f"  Booking ID  : #{booking.id}\n"
        f"  Status      : CANCELLED\n"
    )
    if reason:
        body += f"\nReason:\n{reason}\n"
    body += (
        "\nPlease feel free to reach out to us if you'd like to discuss alternative options "
        "or have any questions.\n\n"
        "Best regards,\nTravel Worthy PH Team"
    )
    _send(subject, [user.email], body)


def send_user_registration_welcome(user) -> None:
    """Send welcome email to newly registered users."""
    subject = "Welcome to Travel Worthy PH!"
    body = (
        f"Hi {user.name},\n\n"
        "Welcome to Travel Worthy PH! Your account has been successfully created.\n\n"
        "You can now:\n"
        "  • Browse and book amazing travel packages\n"
        "  • Submit custom trip inquiries\n"
        "  • View your bookings and travel history\n"
        "  • Save your favorite packages\n\n"
        "Start exploring our collection of unforgettable travel experiences!\n\n"
        "Best regards,\nTravel Worthy PH Team"
    )
    _send(subject, [user.email], body)


def send_inquiry_reply(inquiry, admin_response: str) -> None:
    """Send email to customer when admin replies to their inquiry."""
    package_ref = f" {inquiry.package.title}" if inquiry.package_id and inquiry.package else ""
    subject = f"Re: Your Trip Inquiry to {inquiry.destination}"
    body = (
        f"Hi {inquiry.name},\n\n"
        f"Thank you for your interest in our {inquiry.destination}{package_ref} package!\n\n"
        f"Here's our response to your inquiry:\n\n"
        f"{admin_response}\n\n"
        "If you have any further questions, please don't hesitate to reach out.\n\n"
        "Best regards,\nTravel Worthy PH Team"
    )
    _send(subject, [inquiry.email], body)


def send_booking_cancellation(user, booking, package) -> None:
    """Send email when a booking is cancelled."""
    subject = f"Booking Cancelled — {package.title}"
    body = (
        f"Hi {user.name},\n\n"
        f"Your booking for '{package.title}' has been cancelled.\n\n"
        f"  Booking ID  : #{booking.id}\n"
        f"  Travel date : {booking.travel_date.strftime('%B %d, %Y')}\n"
        f"  Status      : CANCELLED\n\n"
        "If you'd like to rebook or need assistance, please contact us anytime.\n\n"
        "Thank you,\nTravel Worthy PH Team"
    )
    _send(subject, [user.email], body)


def send_inquiry_receipt(inquiry) -> None:
    """Send immediate receipt confirmation to customer after inquiry submission.
    
    Includes:
    - Confirmation that inquiry was received
    - Unique reference number for tracking
    - Link to track inquiry status (no login required)
    - Expected response time
    
    Args:
        inquiry: The Inquiry object that was just created
    """
    subject = f"We received your {inquiry.destination} inquiry!"
    tracking_url = f"{current_app.config.get('SITE_URL', 'https://travelworthyph.com')}/inquiry/{inquiry.reference_number}"
    
    body = (
        f"Hi {inquiry.name},\n\n"
        f"Thank you for your interest in our {inquiry.destination} trip!\n\n"
        f"We've received your inquiry and our team is already reviewing it.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Your Inquiry Reference: {inquiry.reference_number}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Destination        : {inquiry.destination}\n"
        f"Travel Dates       : {inquiry.travel_date_from.strftime('%B %d')} - {inquiry.travel_date_to.strftime('%B %d, %Y')}\n"
        f"Travelers          : {inquiry.num_adults} adult(s), {inquiry.num_children} child(ren), {inquiry.num_infants} infant(s)\n\n"
        f"📍 TRACK YOUR STATUS\n"
        f"You can check your inquiry status anytime using your reference number:\n"
        f"{tracking_url}\n\n"
        f"⏱️  EXPECTED RESPONSE TIME\n"
        f"We typically respond to all inquiries within 24-48 business hours.\n"
        f"Our team will send personalized recommendations with:\n"
        f"  ✓ Tailored package suggestions\n"
        f"  ✓ Pricing & availability\n"
        f"  ✓ Visa requirements\n"
        f"  ✓ Next steps to finalize your booking\n\n"
        f"🌍 IN THE MEANTIME\n"
        f"Feel free to explore:\n"
        f"  • Our travel blog for destination tips\n"
        f"  • Visa requirements for {inquiry.destination}\n"
        f"  • Similar package recommendations\n\n"
        f"Questions? Feel free to reply to this email or contact us directly.\n\n"
        f"Best regards,\n"
        f"Travel Worthy PH Team\n"
        f"✈️ Making Your Travel Dreams Real"
    )
    _send(subject, [inquiry.email], body)
