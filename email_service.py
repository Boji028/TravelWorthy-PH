"""Centralised email sending helpers."""
import os
import re
from html import escape as html_escape
from urllib.parse import quote_plus


def _strip_headers(value: str) -> str:
    """Remove CRLF sequences to prevent SMTP header injection."""
    return re.sub(r'[\r\n]+', ' ', value).strip()

from flask import current_app, render_template_string, request
from flask_mail import Message
from app import mail


def _send(subject: str, recipients: list, body: str, html: str = None, cc: list = None) -> None:
    """Send an email, silently failing if mail is not configured."""
    if not current_app.config.get('MAIL_USERNAME'):
        return  # Mail not configured — skip silently
    try:
        msg = Message(subject=subject, recipients=recipients, body=body, html=html, cc=cc or None)
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Email send error: {e}")


def send_contact_autoreply(name: str, to_email: str, subject: str) -> None:
    name = _strip_headers(name)
    subject = _strip_headers(subject)
    reply_subject = f"Re: {subject}"
    safe_name = html_escape(name)
    safe_subject = html_escape(subject)
    logo_url = "https://res.cloudinary.com/dbcjxuxhl/image/upload/brand_logo_ip0yv0.png"
    body = (
        f"Dear {name},\n\n"
        "Thank you for contacting Travel Worthy PH. This is to confirm that we have "
        "received your inquiry and a representative will respond within 24 hours.\n\n"
        "For immediate assistance:\n"
        "  Phone / SMS  : +63 917 824 7128\n"
        "  Email        : travelworthyph@gmail.com\n"
        "  Facebook     : facebook.com/travelworthyph\n"
        "  Office Hours : Monday – Sunday | 9:00 AM – 6:00 PM\n\n"
        "Sincerely,\nTravel Worthy PH"
    )
    html = f"""
    <html><body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px;">
      <tr><td>

        <!-- BODY -->
        <p style="font-size:14px;color:#222222;margin:0 0 14px;">Dear <strong>{safe_name}</strong>,</p>
        <p style="font-size:14px;color:#444444;line-height:1.7;margin:0 0 14px;">
          Thank you for contacting <strong>Travel Worthy PH</strong>. This is to confirm that we have
          received your inquiry regarding <em>"{safe_subject}"</em> and a representative will
          respond to you within <strong>24 hours</strong>.
        </p>
        <p style="font-size:14px;color:#444444;line-height:1.7;margin:0 0 10px;">
          For immediate assistance, you may reach us through any of the following:
        </p>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 20px 8px;">
          <tr><td style="font-size:14px;color:#444444;padding:3px 0;">📞&nbsp; <strong>Phone / SMS</strong>&nbsp;:&nbsp; +63 917 824 7128</td></tr>
          <tr><td style="font-size:14px;color:#444444;padding:3px 0;">📧&nbsp; <strong>Email</strong>&nbsp;:&nbsp; travelworthyph@gmail.com</td></tr>
          <tr><td style="font-size:14px;color:#444444;padding:3px 0;">📘&nbsp; <strong>Facebook</strong>&nbsp;:&nbsp; <a href="https://facebook.com/travelworthyph" style="color:#175968;">facebook.com/travelworthyph</a></td></tr>
          <tr><td style="font-size:14px;color:#444444;padding:3px 0;">🕐&nbsp; <strong>Office Hours</strong>&nbsp;:&nbsp; Monday – Sunday | 9:00 AM – 6:00 PM</td></tr>
        </table>
        <p style="font-size:14px;color:#444444;margin:0 0 4px;">Sincerely,</p>
        <p style="font-size:14px;color:#444444;margin:0 0 28px;"><strong>Travel Worthy PH Team</strong></p>

        <!-- SIGNATURE -->
        <table width="100%" cellpadding="0" cellspacing="0" style="border-top:2px solid #f5a623;">
          <tr>
            <td width="160" style="background:#ffffff;padding:10px 12px;vertical-align:middle;border:1px solid #eeeeee;">
              <img src="{logo_url}" width="140" height="60"
                style="display:block;object-fit:contain;" alt="Travel Worthy PH" />
            </td>
            <td style="padding:12px 0 12px 16px;vertical-align:middle;">
              <div style="font-size:13px;font-weight:bold;color:#222222;">Admin | Representative</div>
              <div style="font-size:12px;color:#555555;margin-top:3px;">(+63) 936 882 7966</div>
              <div style="margin-top:4px;">
                <a href="https://www.facebook.com/jhakie.travelworthyph/"
                  style="font-size:12px;color:#1a5276;text-decoration:none;">
                  https://www.facebook.com/jhakie.travelworthyph/
                </a>
              </div>
              <div style="margin-top:3px;">
                <a href="https://www.google.com/maps/place/WalterMart+Batangas/@13.7637654,121.0538241,17z"
                  style="font-size:12px;color:#555555;text-decoration:none;">
                  3F Waltermart Batangas, Batangas City, Philippines 4200
                </a>
              </div>
            </td>
          </tr>
        </table>

        <!-- DISCLAIMER -->
        <p style="font-size:10px;color:#999999;line-height:1.6;margin-top:12px;
                  border-top:1px solid #eeeeee;padding-top:10px;">
          This e-mail message (including attachments, if any) is intended for the use of the individual
          or the entity to whom it is addressed and may contain information that is privileged, proprietary,
          confidential and exempt from disclosure. If you are not the intended recipient, you are notified
          that any dissemination, distribution or copying of this communication is strictly prohibited.
          If you have received this communication in error, please notify the sender and delete this
          e-mail message immediately.
        </p>

      </td></tr>
    </table>
    </body></html>
    """
    _send(reply_subject, [to_email], body, html=html)


def send_contact_admin_alert(admin_email: str, name: str, email: str, subject: str, message: str) -> None:
    name = _strip_headers(name)
    subject = _strip_headers(subject)
    alert_subject = f"[Admin] New Contact Message: {subject}"
    body = (
        f"New contact form submission.\n\n"
        f"  From    : {name} ({email})\n"
        f"  Subject : {subject}\n\n"
        f"  Message :\n{message}\n"
    )
    _send(alert_subject, [admin_email], body)


def send_user_registration_welcome(user) -> None:
    """Send welcome email to newly registered users."""
    subject = "Welcome to Travel Worthy PH!"
    body = (
        f"Hi {user.name},\n\n"
        "Welcome to Travel Worthy PH! Your account has been successfully created.\n\n"
        "You can now:\n"
        "  • Browse our travel packages\n"
        "  • Submit custom trip inquiries\n"
        "  • Track your inquiry status anytime\n"
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


def send_admin_new_inquiry(admin_email: str, inquiry, base_url: str = None) -> None:
    """Notify admin when a customer submits a new inquiry.

    If the inquiry's package has an assigned agent, that agent is CC'd
    automatically so they're looped in without Admin needing to forward it.
    Visa inquiries (no package, tagged '[FOR VISA]' in special_requests)
    instead CC the single site-wide visa agent, if one is configured.

    Args:
        base_url: Site base URL used to build the "View in admin panel" link
            in the HTML version. Pass this explicitly when calling from
            outside a request context (e.g. a background thread) —
            `request.host_url` is only available during a request. If
            omitted (and unavailable from config/request), the email still
            sends, just without the button.
    """
    package_ref = f" [{inquiry.package.title}]" if inquiry.package_id and inquiry.package else ""
    subject = f"[Admin] New Inquiry: {inquiry.destination}{package_ref} — {inquiry.reference_number}"

    is_visa = bool(inquiry.special_requests and inquiry.special_requests.startswith('[FOR VISA]'))

    # --- Plain text body (unchanged) ---
    body = (
        f"A new trip inquiry has been submitted.\n\n"
        f"  Reference : {inquiry.reference_number}\n"
        f"  Name      : {inquiry.name}\n"
        f"  Email     : {inquiry.email}\n"
        f"  Phone     : {inquiry.contact_number}\n"
        f"  Destination: {inquiry.destination}\n"
    )
    cc_list = None
    agent_name = None
    if inquiry.package_id and inquiry.package:
        body += f"  Package   : {inquiry.package.title}\n"
        agent = inquiry.package.assigned_agent
        if agent and agent.is_active and agent.email:
            cc_list = [agent.email]
            agent_name = agent.name
            body += f"  Assigned agent: {agent.name} (CC'd on this email)\n"
    elif is_visa:
        from models.agent import Agent
        agent = Agent.query.filter_by(is_visa_agent=True, is_active=True).first()
        if agent and agent.email:
            cc_list = [agent.email]
            agent_name = agent.name
            body += f"  Inquiry type: Visa request\n"
            body += f"  Assigned agent: {agent.name} (CC'd on this email)\n"
    body += (
        f"  Dates     : {inquiry.travel_date_from.strftime('%b %d')} — "
        f"{inquiry.travel_date_to.strftime('%b %d, %Y')}\n"
        f"  Pax       : {inquiry.num_adults} adult(s), "
        f"{inquiry.num_children} child(ren), {inquiry.num_infants} infant(s)\n"
    )
    if inquiry.special_requests:
        body += f"\nSpecial requests:\n{inquiry.special_requests}\n"

    # --- HTML version (Option A — minimal brand bar) ---
    if base_url is None:
        base_url = current_app.config.get('SITE_URL') or (request.host_url if request else None)

    # NOTE: adjust this path/query param if the admin Inquiries page uses a
    # different search param name — this assumes ?search=<reference_number>
    # matches the AJAX filter already built into that page.
    admin_link = None
    if base_url:
        admin_link = (
            f"{base_url.rstrip('/')}/admin/inquiries"
            f"?search={quote_plus(inquiry.reference_number)}"
        )

    logo_url = "https://res.cloudinary.com/dbcjxuxhl/image/upload/brand_logo_ip0yv0.png"
    safe_ref = html_escape(inquiry.reference_number)

    rows = [
        ("Name", html_escape(inquiry.name)),
        ("Email", html_escape(inquiry.email)),
        ("Phone", html_escape(inquiry.contact_number)),
        ("Destination", html_escape(inquiry.destination)),
    ]
    if inquiry.package_id and inquiry.package:
        rows.append(("Package", html_escape(inquiry.package.title)))
    elif is_visa:
        rows.append(("Type", "Visa request"))
    rows.append((
        "Dates",
        f"{inquiry.travel_date_from.strftime('%b %d')} – "
        f"{inquiry.travel_date_to.strftime('%b %d, %Y')}"
    ))
    rows.append((
        "Pax",
        f"{inquiry.num_adults} adult(s), {inquiry.num_children} child(ren), "
        f"{inquiry.num_infants} infant(s)"
    ))

    rows_html = "".join(
        f'<tr><td style="padding:5px 0;color:#8fa8a3;width:110px;">{label}</td>'
        f'<td style="padding:5px 0;">{value}</td></tr>'
        for label, value in rows
    )

    agent_badge_html = ""
    if agent_name:
        agent_badge_html = (
            '<div style="margin:14px 0;">'
            '<span style="display:inline-block;background:#e1f5ee;color:#085041;'
            'font-size:11px;font-weight:bold;padding:4px 10px;border-radius:12px;">'
            f"Agent CC'd: {html_escape(agent_name)}</span></div>"
        )

    special_requests_html = ""
    if inquiry.special_requests:
        special_requests_html = (
            '<div style="background:#ede5d8;border-radius:6px;padding:10px 12px;'
            'font-size:12px;color:#424142;margin-bottom:18px;">'
            f"{html_escape(inquiry.special_requests)}</div>"
        )

    cta_html = ""
    if admin_link:
        cta_html = (
            f'<a href="{admin_link}" style="display:inline-block;background:#EF8233;'
            'color:#ffffff;font-size:13px;font-weight:bold;padding:10px 20px;'
            'border-radius:6px;text-decoration:none;">View in admin panel &rarr;</a>'
        )

    html = f"""
    <html><body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:4px;background:#175968;line-height:4px;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:20px 24px;background:#fdfaf6;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td><img src="{logo_url}" width="110" style="display:block;" alt="Travel Worthy PH" /></td>
            <td align="right" style="font-size:11px;color:#8fa8a3;letter-spacing:0.5px;">NEW INQUIRY</td>
          </tr>
        </table>
        <p style="font-size:13px;color:#424142;margin:18px 0 4px;">Reference</p>
        <p style="font-size:20px;font-weight:bold;color:#175968;margin:0 0 18px;">{safe_ref}</p>
        <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;">
          {rows_html}
        </table>
        {agent_badge_html}
        {special_requests_html}
        {cta_html}
      </td></tr>
    </table>
    </body></html>
    """

    _send(subject, [admin_email], body, html=html, cc=cc_list)


def send_inquiry_confirmed(inquiry) -> None:
    """Notify customer when admin confirms their inquiry (slot reserved)."""
    package_ref = f" for {inquiry.package.title}" if inquiry.package_id and inquiry.package else ""
    subject = f"Your {inquiry.destination} inquiry has been confirmed! — {inquiry.reference_number}"
    base_url = current_app.config.get('SITE_URL', request.host_url).rstrip('/')
    tracking_url = f"{base_url}/inquiry/{inquiry.reference_number}"
    body = (
        f"Hi {inquiry.name},\n\n"
        f"Great news! Your trip inquiry{package_ref} to {inquiry.destination} "
        f"has been confirmed by our team.\n\n"
        f"  Reference  : {inquiry.reference_number}\n"
        f"  Destination: {inquiry.destination}\n"
        f"  Dates      : {inquiry.travel_date_from.strftime('%B %d')} — "
        f"{inquiry.travel_date_to.strftime('%B %d, %Y')}\n"
        f"  Travelers  : {inquiry.num_adults} adult(s), "
        f"{inquiry.num_children} child(ren), {inquiry.num_infants} infant(s)\n\n"
        f"Your slot has been reserved. Our representative will be in touch shortly "
        f"with the next steps to finalize your booking.\n\n"
        f"Track your inquiry anytime:\n{tracking_url}\n\n"
        f"For immediate assistance:\n"
        f"  Phone / SMS  : +63 917 824 7128\n"
        f"  Email        : travelworthyph@gmail.com\n"
        f"  Office Hours : Monday – Sunday | 9:00 AM – 6:00 PM\n\n"
        f"Sincerely,\nTravel Worthy PH Team\n"
        f"✈️ Making Your Travel Dreams Real"
    )
    _send(subject, [inquiry.email], body)


def send_inquiry_receipt(inquiry, base_url: str = None) -> None:
    """Send immediate receipt confirmation to customer after inquiry submission.
    
    Includes:
    - Confirmation that inquiry was received
    - Unique reference number for tracking
    - Link to track inquiry status (no login required)
    - Expected response time
    
    Args:
        inquiry: The Inquiry object that was just created
        base_url: Site base URL for the tracking link. Pass this explicitly
            when calling from outside a request context (e.g. a background
            thread) — `request.host_url` is only available during a request.
    """
    subject = f"We received your {inquiry.destination} inquiry!"
    if base_url is None:
        base_url = current_app.config.get('SITE_URL') or request.host_url
    base_url = base_url.rstrip('/')
    tracking_url = f"{base_url}/inquiry/{inquiry.reference_number}"
    
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
        f"📞 WANT TO START THE CONVERSATION NOW?\n"
        f"You don't have to wait — reach out directly anytime:\n"
        f"  Phone / SMS  : +63 917 824 7128\n"
        f"  Email        : travelworthyph@gmail.com\n"
        f"  Facebook     : facebook.com/travelworthyph\n"
        f"  Instagram    : instagram.com/travelworthyph\n"
        f"  TikTok       : tiktok.com/@travelworthyph\n"
        f"  Office Hours : Monday – Sunday | 9:00 AM – 6:00 PM\n\n"
        f"Best regards,\n"
        f"Travel Worthy PH Team\n"
        f"✈️ Making Your Travel Dreams Real"
    )
    _send(subject, [inquiry.email], body)


def send_inquiry_emails_async(inquiry_id: int, base_url: str) -> None:
    """Send the customer receipt and admin alert for a new inquiry in a
    background thread, so the request returns immediately instead of
    waiting on two sequential SMTP round trips (the actual cause of slow
    inquiry submissions — each mail.send() opens its own connection to
    Gmail's SMTP server, which alone can take a couple seconds).

    base_url must be captured from the original request before spawning the
    thread — Flask's `request` object isn't available outside a request
    context, which a background thread never has.
    """
    from threading import Thread
    app = current_app._get_current_object()

    def _worker():
        with app.app_context():
            from app import db
            from models.inquiry import Inquiry
            inquiry = db.session.get(Inquiry, inquiry_id)
            if not inquiry:
                return
            try:
                send_inquiry_receipt(inquiry, base_url=base_url)
                admin_email = os.getenv('ADMIN_EMAIL', '')
                if admin_email:
                    send_admin_new_inquiry(admin_email, inquiry, base_url=base_url)
            except Exception as e:
                app.logger.warning(
                    f"Email notification failed for inquiry #{inquiry_id}: {e}", exc_info=True
                )

    Thread(target=_worker, daemon=True).start()
