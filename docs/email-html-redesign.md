# Inquiry email HTML redesign

## What changed

### email_service.py
- send_admin_new_inquiry() — added HTML version (Option A: minimal brand bar),
  gained optional base_url parameter passed through from send_inquiry_emails_async().
  CTA button links to /admin/inquiries?search={reference_number}.
- send_inquiry_receipt() — added HTML version matching existing plain-text wording.
  Branches on [FOR VISA] flag (same check used by admin alert CC routing) to swap
  in visa-specific copy: subject, intro line, expected response items, and
  in-the-meantime bullets. Tour inquiries unaffected.
  Phone/SMS expanded to six numbers.
- send_inquiry_confirmed() — added HTML version with teal confirmed badge,
  linen key-value box, tracking button, contact table, signature footer.
- Branches on [FOR VISA] flag: subject and intro line swap to visa-specific
  wording ("visa inquiry for {destination}") for visa inquiries.
  Package inquiries and trip inquiries unaffected.
- Phone/SMS expanded to six numbers matching the receipt email.
- Admin now receives a copy when an inquiry is confirmed, styled with the
  same minimal brand bar as the admin new-inquiry alert, with the confirmed
  badge. Assigned agent (package or visa) is CC'd using the same routing
  logic as send_admin_new_inquiry().s

## Things to verify
- Admin inquiries search param: CTA button assumes ?search= is the correct
  param name on the admin inquiries page.
- Any pytest mock asserting _send() call signatures without html= kwarg
  will need updating.

## Files changed
- email_service.py

### send_contact_autoreply()
- Replaced old signature block (Admin | Representative card) with the
  simple amber-line footer matching all other emails.
- Phone/SMS expanded to six numbers.

### send_contact_admin_alert()
- Added HTML version with brand bar, NEW MESSAGE label, from/email/subject
  key-value table, linen message body box, amber Reply to sender button
  that mailto: links directly to the customer email.