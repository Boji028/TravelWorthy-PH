"""Centralised email sending helpers."""
import os
import re
from html import escape as html_escape
from urllib.parse import quote_plus


def _strip_headers(value: str) -> str:
    """Remove CRLF sequences to prevent SMTP header injection."""
    return re.sub(r"[\r\n]+", " ", value).strip()


from flask import current_app, render_template_string, request
from flask_mail import Message
from app import mail


def _send(subject: str, recipients: list, body: str, html: str = None, cc: list = None) -> bool:
    """Send an email, silently failing if mail is not configured.

    Returns True if the send succeeded, False otherwise (mail not
    configured, or the actual send raised). Never raises itself -
    existing callers that don't check the return value keep their
    original fire-and-forget behavior unchanged; send_inquiry_receipt()
    is the one caller that does check it, to surface a failed customer
    confirmation rather than leaving it silent.
    """
    if not current_app.config.get("MAIL_USERNAME"):
        return False  # Mail not configured — skip silently
    try:
        msg = Message(subject=_strip_headers(subject), recipients=recipients, body=body, html=html, cc=cc or None)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Email send error: {e}")
        return False


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

    is_visa = bool(inquiry.special_requests and inquiry.special_requests.startswith("[FOR VISA]"))

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
        base_url = current_app.config.get("SITE_URL") or (request.host_url if request else None)

    # NOTE: adjust this path/query param if the admin Inquiries page uses a
    # different search param name — this assumes ?search=<reference_number>
    # matches the AJAX filter already built into that page.
    admin_link = None
    if base_url:
        admin_link = f"{base_url.rstrip('/')}/admin/inquiries" f"?search={quote_plus(inquiry.reference_number)}"

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
    rows.append(
        ("Dates", f"{inquiry.travel_date_from.strftime('%b %d')} – " f"{inquiry.travel_date_to.strftime('%b %d, %Y')}")
    )
    rows.append(
        ("Pax", f"{inquiry.num_adults} adult(s), {inquiry.num_children} child(ren), " f"{inquiry.num_infants} infant(s)")
    )

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
            "color:#ffffff;font-size:13px;font-weight:bold;padding:10px 20px;"
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
    is_visa = bool(not inquiry.package_id and inquiry.special_requests and inquiry.special_requests.startswith("[FOR VISA]"))
    package_ref = f" for {inquiry.package.title}" if inquiry.package_id and inquiry.package else ""
    subject = (
        f"Your visa inquiry for {inquiry.destination} has been confirmed! — {inquiry.reference_number}"
        if is_visa
        else f"Your {inquiry.destination} inquiry has been confirmed! — {inquiry.reference_number}"
    )
    # `or` form, not .get(key, default): the default arg evaluates
    # request.host_url even when SITE_URL is set, which raises if this is
    # ever called outside a request context (as the other senders here can be).
    base_url = (current_app.config.get("SITE_URL") or request.host_url).rstrip("/")
    tracking_url = f"{base_url}/inquiry/{inquiry.reference_number}"
    body = (
        f"Hi {inquiry.name},\n\n"
        f"Great news! Your {'visa inquiry for' if is_visa else f'trip inquiry{package_ref} to'} "
        f"{inquiry.destination} has been confirmed by our team.\n\n"
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
        f"  Phone / SMS  : +63 917 824 7128 (Main)\n"
        f"                 +63 966 088 7036 (Visa Agent)\n"
        f"                 +63 930 672 8009 (Domestic Agent)\n"
        f"                 +63 929 235 4375 (International Agent)\n"
        f"                 +63 951 920 9456 (International Agent)\n"
        f"                 +63 918 905 0610 (International Agent)\n"
        f"  Email        : travelworthyph@gmail.com\n"
        f"  Office Hours : Monday – Sunday | 9:00 AM – 6:00 PM\n\n"
        f"Sincerely,\nTravel Worthy PH Team\n"
        f"✈️ Making Your Travel Dreams Real"
    )

    # --- HTML version (original wording, styled layout) ---
    logo_url = "https://res.cloudinary.com/dbcjxuxhl/image/upload/brand_logo_ip0yv0.png"
    safe_name = html_escape(inquiry.name)
    safe_destination = html_escape(inquiry.destination)
    safe_ref = html_escape(inquiry.reference_number)
    safe_package_ref = html_escape(package_ref)
    dates_str = f"{inquiry.travel_date_from.strftime('%B %d')} — " f"{inquiry.travel_date_to.strftime('%B %d, %Y')}"
    pax_str = f"{inquiry.num_adults} adult(s), {inquiry.num_children} child(ren), " f"{inquiry.num_infants} infant(s)"

    html = f"""
    <html><body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:4px;background:#175968;line-height:4px;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:22px 26px;background:#fdfaf6;">

        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px;">
          <tr>
            <td><img src="{logo_url}" width="110" style="display:block;" alt="Travel Worthy PH" /></td>
            <td align="right"><span style="display:inline-block;background:#e1f5ee;color:#085041;font-size:11px;font-weight:bold;padding:4px 10px;border-radius:12px;">&#10003; CONFIRMED</span></td>
          </tr>
        </table>

        <p style="font-size:15px;color:#222222;margin:0 0 4px;">Hi {safe_name},</p>
        <p style="font-size:14px;color:#444444;line-height:1.6;margin:0 0 20px;">Great news! Your {'visa inquiry for' if is_visa else f'trip inquiry{safe_package_ref} to'} <strong>{safe_destination}</strong> has been confirmed by our team.</p>

        <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;background:#ede5d8;border-radius:6px;margin-bottom:20px;">
          <tr><td style="padding:10px 14px;color:#8fa8a3;width:100px;">Reference</td><td style="padding:10px 14px 10px 0;font-weight:bold;color:#175968;">{safe_ref}</td></tr>
          <tr><td style="padding:0 14px 10px;color:#8fa8a3;">Destination</td><td style="padding:0 14px 10px 0;">{safe_destination}</td></tr>
          <tr><td style="padding:0 14px 10px;color:#8fa8a3;">Dates</td><td style="padding:0 14px 10px 0;">{dates_str}</td></tr>
          <tr><td style="padding:0 14px 10px;color:#8fa8a3;">Travelers</td><td style="padding:0 14px 10px 0;">{pax_str}</td></tr>
        </table>

        <p style="font-size:13px;color:#444444;line-height:1.6;margin:0 0 20px;">Your slot has been reserved. Our representative will be in touch shortly with the next steps to finalize your booking.</p>

        <p style="font-size:12px;color:#8fa8a3;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 8px;">Track your inquiry anytime</p>
        <a href="{tracking_url}" style="display:inline-block;background:#EF8233;color:#ffffff;font-size:13px;font-weight:bold;padding:9px 18px;border-radius:6px;text-decoration:none;margin-bottom:22px;">View inquiry status &rarr;</a>

        <p style="font-size:12px;color:#8fa8a3;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 8px;">For immediate assistance</p>
        <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;margin-bottom:22px;">
          <tr><td style="padding:3px 0;color:#8fa8a3;width:110px;vertical-align:top;">Phone / SMS</td><td style="padding:3px 0;line-height:1.7;">+63 917 824 7128 (Main)<br/>+63 966 088 7036 (Visa Agent)<br/>+63 930 672 8009 (Domestic Agent)<br/>+63 929 235 4375 (International Agent)<br/>+63 951 920 9456 (International Agent)<br/>+63 918 905 0610 (International Agent)</td></tr>
          <tr><td style="padding:3px 0;color:#8fa8a3;">Email</td><td><a href="mailto:travelworthyph@gmail.com" style="color:#175968;text-decoration:none;">travelworthyph@gmail.com</a></td></tr>
          <tr><td style="padding:3px 0;color:#8fa8a3;">Office Hours</td><td>Monday – Sunday | 9:00 AM – 6:00 PM</td></tr>
        </table>

        <table width="100%" cellpadding="0" cellspacing="0" style="border-top:2px solid #f5a623;padding-top:14px;">
          <tr>
            <td>
              <p style="font-size:13px;color:#444444;margin:0 0 2px;">Sincerely,</p>
              <p style="font-size:13px;font-weight:bold;color:#222222;margin:0;">Travel Worthy PH Team</p>
              <p style="font-size:12px;color:#8fa8a3;margin:4px 0 0;">Making Your Travel Dreams Real</p>
            </td>
          </tr>
        </table>

      </td></tr>
    </table>
    </body></html>
    """

    _send(subject, [inquiry.email], body, html=html)

    # Notify admin and CC assigned agent for paper trail.
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if admin_email:
        cc_list = None
        if inquiry.package_id and inquiry.package:
            agent = inquiry.package.assigned_agent
            if agent and agent.is_active and agent.email:
                cc_list = [agent.email]
        elif inquiry.special_requests and inquiry.special_requests.startswith("[FOR VISA]"):
            from models.agent import Agent

            agent = Agent.query.filter_by(is_visa_agent=True, is_active=True).first()
            if agent and agent.email:
                cc_list = [agent.email]

        admin_subject = f"[Admin] Inquiry Confirmed: {inquiry.destination} — {inquiry.reference_number}"
        admin_body = (
            f"The following inquiry has been marked as confirmed.\n\n"
            f"  Reference  : {inquiry.reference_number}\n"
            f"  Customer   : {inquiry.name} ({inquiry.email})\n"
            f"  Phone      : {inquiry.contact_number}\n"
            f"  Destination: {inquiry.destination}\n"
            f"  Dates      : {inquiry.travel_date_from.strftime('%b %d')} — "
            f"{inquiry.travel_date_to.strftime('%b %d, %Y')}\n"
            f"  Pax        : {inquiry.num_adults} adult(s), "
            f"{inquiry.num_children} child(ren), {inquiry.num_infants} infant(s)\n"
        )
        if cc_list:
            admin_body += f"  Agent CC'd : {cc_list[0]}\n"

        safe_ref = html_escape(inquiry.reference_number)
        safe_name = html_escape(inquiry.name)
        safe_destination = html_escape(inquiry.destination)
        safe_email = html_escape(inquiry.email)
        safe_phone = html_escape(inquiry.contact_number)
        logo_url = "https://res.cloudinary.com/dbcjxuxhl/image/upload/brand_logo_ip0yv0.png"
        dates_str = f"{inquiry.travel_date_from.strftime('%b %d')} — " f"{inquiry.travel_date_to.strftime('%b %d, %Y')}"
        pax_str = f"{inquiry.num_adults} adult(s), {inquiry.num_children} child(ren), " f"{inquiry.num_infants} infant(s)"
        agent_badge_html = ""
        if cc_list:
            agent_badge_html = (
                '<div style="margin:14px 0;">'
                '<span style="display:inline-block;background:#e1f5ee;color:#085041;'
                'font-size:11px;font-weight:bold;padding:4px 10px;border-radius:12px;">'
                f"Agent CC'd: {html_escape(cc_list[0])}</span></div>"
            )

        admin_html = f"""
        <html><body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr><td style="height:4px;background:#175968;line-height:4px;font-size:0;">&nbsp;</td></tr>
          <tr><td style="padding:20px 24px;background:#fdfaf6;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td><img src="{logo_url}" width="110" style="display:block;" alt="Travel Worthy PH" /></td>
                <td align="right"><span style="display:inline-block;background:#e1f5ee;color:#085041;
                  font-size:11px;font-weight:bold;padding:4px 10px;border-radius:12px;">&#10003; CONFIRMED</span></td>
              </tr>
            </table>
            <p style="font-size:13px;color:#424142;margin:18px 0 4px;">Reference</p>
            <p style="font-size:20px;font-weight:bold;color:#175968;margin:0 0 18px;">{safe_ref}</p>
            <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;">
              <tr><td style="padding:5px 0;color:#8fa8a3;width:110px;">Customer</td><td style="padding:5px 0;">{safe_name}</td></tr>
              <tr><td style="padding:5px 0;color:#8fa8a3;">Email</td><td style="padding:5px 0;">{safe_email}</td></tr>
              <tr><td style="padding:5px 0;color:#8fa8a3;">Phone</td><td style="padding:5px 0;">{safe_phone}</td></tr>
              <tr><td style="padding:5px 0;color:#8fa8a3;">Destination</td><td style="padding:5px 0;">{safe_destination}</td></tr>
              <tr><td style="padding:5px 0;color:#8fa8a3;">Dates</td><td style="padding:5px 0;">{dates_str}</td></tr>
              <tr><td style="padding:5px 0;color:#8fa8a3;">Pax</td><td style="padding:5px 0;">{pax_str}</td></tr>
            </table>
            {agent_badge_html}
          </td></tr>
        </table>
        </body></html>
        """
        _send(admin_subject, [admin_email], admin_body, html=admin_html, cc=cc_list)


def send_inquiry_receipt(inquiry, base_url: str = None) -> bool:
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

    Returns:
        True if the email actually sent, False otherwise (mail not
        configured, or the send failed) — send_inquiry_emails_async uses
        this to flag Inquiry.confirmation_email_failed.
    """
    is_visa = bool(not inquiry.package_id and inquiry.special_requests and inquiry.special_requests.startswith("[FOR VISA]"))

    subject = (
        f"We received your visa inquiry for {inquiry.destination}!"
        if is_visa
        else f"We received your {inquiry.destination} inquiry!"
    )
    if base_url is None:
        base_url = current_app.config.get("SITE_URL") or request.host_url
    base_url = base_url.rstrip("/")
    tracking_url = f"{base_url}/inquiry/{inquiry.reference_number}"

    if is_visa:
        intro_line = f"Thank you for your interest in securing a visa for {inquiry.destination}!\n\n"
        response_intro = (
            f"We typically respond to all visa inquiries within 24-48 business hours.\n" f"Our team will send you:\n"
        )
        response_items = (
            f"  ✓ Document checklist for your application\n"
            f"  ✓ Application requirements & fees\n"
            f"  ✓ Estimated processing timeline\n"
            f"  ✓ Next steps to file your application\n\n"
        )
        meantime_items = f"  • Our travel blog for destination tips\n" f"  • Other destinations we assist with visas for\n\n"
    else:
        intro_line = f"Thank you for your interest in our {inquiry.destination} trip!\n\n"
        response_intro = (
            f"We typically respond to all inquiries within 24-48 business hours.\n"
            f"Our team will send personalized recommendations with:\n"
        )
        response_items = (
            f"  ✓ Tailored package suggestions\n"
            f"  ✓ Pricing & availability\n"
            f"  ✓ Visa requirements\n"
            f"  ✓ Next steps to finalize your booking\n\n"
        )
        meantime_items = (
            f"  • Our travel blog for destination tips\n"
            f"  • Visa requirements for {inquiry.destination}\n"
            f"  • Similar package recommendations\n\n"
        )

    body = (
        f"Hi {inquiry.name},\n\n"
        f"{intro_line}"
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
        f"{response_intro}"
        f"{response_items}"
        f"🌍 IN THE MEANTIME\n"
        f"Feel free to explore:\n"
        f"{meantime_items}"
        f"📞 WANT TO START THE CONVERSATION NOW?\n"
        f"You don't have to wait — reach out directly anytime:\n"
        f"  Phone / SMS  : +63 917 824 7128 (Main)\n"
        f"                 +63 966 088 7036 (Visa Agent)\n"
        f"                 +63 930 672 8009 (Domestic Agent)\n"
        f"                 +63 929 235 4375 (International Agent)\n"
        f"                 +63 951 920 9456 (International Agent)\n"
        f"                 +63 918 905 0610 (International Agent)\n"
        f"  Email        : travelworthyph@gmail.com\n"
        f"  Facebook     : facebook.com/travelworthyph\n"
        f"  Instagram    : instagram.com/travelworthyph\n"
        f"  TikTok       : tiktok.com/@travelworthyph\n"
        f"  Office Hours : Monday – Sunday | 9:00 AM – 6:00 PM\n\n"
        f"Best regards,\n"
        f"Travel Worthy PH Team\n"
        f"✈️ Making Your Travel Dreams Real"
    )

    # --- HTML version (original wording, styled layout) ---
    logo_url = "https://res.cloudinary.com/dbcjxuxhl/image/upload/brand_logo_ip0yv0.png"
    safe_name = html_escape(inquiry.name)
    safe_destination = html_escape(inquiry.destination)
    safe_ref = html_escape(inquiry.reference_number)
    dates_str = f"{inquiry.travel_date_from.strftime('%B %d')} - " f"{inquiry.travel_date_to.strftime('%B %d, %Y')}"
    pax_str = f"{inquiry.num_adults} adult(s), {inquiry.num_children} child(ren), " f"{inquiry.num_infants} infant(s)"

    if is_visa:
        badge_html = (
            '<td align="right"><span style="display:inline-block;background:#faeeda;'
            "color:#633806;font-size:11px;font-weight:bold;padding:4px 10px;"
            'border-radius:12px;">VISA INQUIRY</span></td>'
        )
        intro_html = f"Thank you for your interest in securing a visa for {safe_destination}!"
        response_intro_html = (
            "We typically respond to all visa inquiries within 24-48 business hours. " "Our team will send you:"
        )
        response_rows_html = (
            '<tr><td style="padding:3px 0;width:18px;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Document checklist for your application</td></tr>'
            '<tr><td style="padding:3px 0;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Application requirements &amp; fees</td></tr>'
            '<tr><td style="padding:3px 0;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Estimated processing timeline</td></tr>'
            '<tr><td style="padding:3px 0;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Next steps to file your application</td></tr>'
        )
        meantime_rows_html = (
            '<tr><td style="padding:3px 0;width:14px;color:#8fa8a3;">&bull;</td>'
            '<td style="padding:3px 0;">Our travel blog for destination tips</td></tr>'
            '<tr><td style="padding:3px 0;color:#8fa8a3;">&bull;</td>'
            '<td style="padding:3px 0;">Other destinations we assist with visas for</td></tr>'
        )
    else:
        badge_html = ""
        intro_html = f"Thank you for your interest in our {safe_destination} trip!"
        response_intro_html = (
            "We typically respond to all inquiries within 24-48 business hours. "
            "Our team will send personalized recommendations with:"
        )
        response_rows_html = (
            '<tr><td style="padding:3px 0;width:18px;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Tailored package suggestions</td></tr>'
            '<tr><td style="padding:3px 0;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Pricing &amp; availability</td></tr>'
            '<tr><td style="padding:3px 0;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Visa requirements</td></tr>'
            '<tr><td style="padding:3px 0;color:#175968;">&#10003;</td>'
            '<td style="padding:3px 0;">Next steps to finalize your booking</td></tr>'
        )
        meantime_rows_html = (
            '<tr><td style="padding:3px 0;width:14px;color:#8fa8a3;">&bull;</td>'
            '<td style="padding:3px 0;">Our travel blog for destination tips</td></tr>'
            f'<tr><td style="padding:3px 0;color:#8fa8a3;">&bull;</td>'
            f'<td style="padding:3px 0;">Visa requirements for {safe_destination}</td></tr>'
            '<tr><td style="padding:3px 0;color:#8fa8a3;">&bull;</td>'
            '<td style="padding:3px 0;">Similar package recommendations</td></tr>'
        )

    html = f"""
    <html><body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:4px;background:#175968;line-height:4px;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:22px 26px;background:#fdfaf6;">

        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px;">
          <tr>
            <td><img src="{logo_url}" width="110" style="display:block;" alt="Travel Worthy PH" /></td>
            {badge_html}
          </tr>
        </table>

        <p style="font-size:15px;color:#222222;margin:0 0 4px;">Hi {safe_name},</p>
        <p style="font-size:14px;color:#444444;line-height:1.6;margin:0 0 4px;">{intro_html}</p>
        <p style="font-size:14px;color:#444444;line-height:1.6;margin:0 0 20px;">We've received your inquiry and our team is already reviewing it.</p>

        <div style="background:#175968;border-radius:6px;padding:14px 18px;margin-bottom:20px;">
          <p style="font-size:11px;color:#9fe1cb;margin:0 0 2px;letter-spacing:0.5px;">YOUR INQUIRY REFERENCE</p>
          <p style="font-size:18px;color:#ffffff;font-weight:bold;margin:0;">{safe_ref}</p>
        </div>

        <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;margin-bottom:20px;">
          <tr><td style="padding:4px 0;color:#8fa8a3;width:110px;">Destination</td><td>{safe_destination}</td></tr>
          <tr><td style="padding:4px 0;color:#8fa8a3;">Travel Dates</td><td>{dates_str}</td></tr>
          <tr><td style="padding:4px 0;color:#8fa8a3;">Travelers</td><td>{pax_str}</td></tr>
        </table>

        <p style="font-size:12px;color:#8fa8a3;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 8px;">Track your status</p>
        <p style="font-size:13px;color:#444444;line-height:1.6;margin:0 0 10px;">You can check your inquiry status anytime using your reference number:</p>
        <a href="{tracking_url}" style="display:inline-block;background:#EF8233;color:#ffffff;font-size:13px;font-weight:bold;padding:9px 18px;border-radius:6px;text-decoration:none;margin-bottom:22px;">View inquiry status &rarr;</a>

        <p style="font-size:12px;color:#8fa8a3;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 8px;">Expected response time</p>
        <p style="font-size:13px;color:#444444;line-height:1.6;margin:0 0 10px;">{response_intro_html}</p>
        <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;margin-bottom:20px;">
          {response_rows_html}
        </table>

        <p style="font-size:12px;color:#8fa8a3;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 8px;">In the meantime</p>
        <p style="font-size:13px;color:#444444;line-height:1.6;margin:0 0 10px;">Feel free to explore:</p>
        <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;margin-bottom:20px;">
          {meantime_rows_html}
        </table>

        <p style="font-size:12px;color:#8fa8a3;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 8px;">Want to start the conversation now?</p>
        <p style="font-size:13px;color:#444444;line-height:1.6;margin:0 0 10px;">You don't have to wait — reach out directly anytime:</p>
        <table style="width:100%;font-size:13px;color:#424142;border-collapse:collapse;margin-bottom:22px;">
          <tr><td style="padding:3px 0;color:#8fa8a3;width:110px;vertical-align:top;">Phone / SMS</td><td style="padding:3px 0;line-height:1.7;">+63 917 824 7128 (Main)<br/>+63 966 088 7036 (Visa Agent)<br/>+63 930 672 8009 (Domestic Agent)<br/>+63 929 235 4375 (International Agent)<br/>+63 951 920 9456 (International Agent)<br/>+63 918 905 0610 (International Agent)</td></tr>
          <tr><td style="padding:3px 0;color:#8fa8a3;">Email</td><td><a href="mailto:travelworthyph@gmail.com" style="color:#175968;text-decoration:none;">travelworthyph@gmail.com</a></td></tr>
          <tr><td style="padding:3px 0;color:#8fa8a3;">Facebook</td><td><a href="https://facebook.com/travelworthyph" style="color:#175968;text-decoration:none;">facebook.com/travelworthyph</a></td></tr>
          <tr><td style="padding:3px 0;color:#8fa8a3;">Instagram</td><td><a href="https://instagram.com/travelworthyph" style="color:#175968;text-decoration:none;">instagram.com/travelworthyph</a></td></tr>
          <tr><td style="padding:3px 0;color:#8fa8a3;">TikTok</td><td><a href="https://tiktok.com/@travelworthyph" style="color:#175968;text-decoration:none;">tiktok.com/@travelworthyph</a></td></tr>
          <tr><td style="padding:3px 0;color:#8fa8a3;">Office Hours</td><td>Monday – Sunday | 9:00 AM – 6:00 PM</td></tr>
        </table>

        <table width="100%" cellpadding="0" cellspacing="0" style="border-top:2px solid #f5a623;padding-top:14px;">
          <tr>
            <td>
              <p style="font-size:13px;color:#444444;margin:0 0 2px;">Best regards,</p>
              <p style="font-size:13px;font-weight:bold;color:#222222;margin:0;">Travel Worthy PH Team</p>
              <p style="font-size:12px;color:#8fa8a3;margin:4px 0 0;">Making Your Travel Dreams Real</p>
            </td>
          </tr>
        </table>

      </td></tr>
    </table>
    </body></html>
    """

    return _send(subject, [inquiry.email], body, html=html)


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

            # Independent try/excepts: these used to share one try block,
            # so a customer-receipt failure meant send_admin_new_inquiry
            # never even ran — the admin wouldn't hear about a new
            # inquiry at all just because the customer's email bounced.
            # Checking the return value (not just catching an exception)
            # matters here: _send(), the low-level helper underneath
            # send_inquiry_receipt, already catches and logs every send
            # failure itself and never re-raises — an except block around
            # the call alone would never actually fire.
            try:
                sent = send_inquiry_receipt(inquiry, base_url=base_url)
                if not sent:
                    inquiry.confirmation_email_failed = True
                    db.session.commit()
            except Exception as e:
                app.logger.warning(f"Customer receipt email failed for inquiry #{inquiry_id}: {e}", exc_info=True)
                inquiry.confirmation_email_failed = True
                db.session.commit()

            admin_email = os.getenv("ADMIN_EMAIL", "")
            if admin_email:
                try:
                    send_admin_new_inquiry(admin_email, inquiry, base_url=base_url)
                except Exception as e:
                    app.logger.warning(f"Admin alert email failed for inquiry #{inquiry_id}: {e}", exc_info=True)

    Thread(target=_worker, daemon=True).start()
