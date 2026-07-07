# Inquiry email HTML redesign — admin alert, customer receipt, customer confirmed

## What changed

Three inquiry-related emails were plain-text only; all three now also send
an HTML version via the `_send()` `html=` argument. Plain-text bodies kept
the same structure as before, so non-HTML mail clients see essentially
what they saw before.

### 1. `send_admin_new_inquiry()` — admin alert (Option A: minimal brand bar)

- 4px teal top bar, logo, "NEW INQUIRY" label
- Reference number in large brand teal
- Key-value table: name, email, phone, destination, package (or "Type:
  Visa request" for visa inquiries), dates, pax
- Teal pill badge when an agent is CC'd: "Agent CC'd: {name}"
- Linen callout box for special requests, only rendered if present
- Amber "View in admin panel →" button →
  `{base_url}/admin/inquiries?search={reference_number}`
- Gained an optional `base_url` parameter; `send_inquiry_emails_async()`
  now passes it through

### 2. `send_inquiry_receipt()` — customer receipt (original wording, restyled)

Restyled with brand styling instead of unicode dividers and emoji section
markers (teal reference box, uppercase label headers, checkmark/bullet
rows, "View inquiry status →" button, real Facebook/Instagram/TikTok
links, signature footer matching the autoreply email).

**Phone numbers:** the "Phone / SMS" line under "Want to start the
conversation now?" now lists six numbers instead of one, stacked on
separate lines in both versions: +63 917 824 7128, +63 929 235 4375,
+63 930 672 8009, +63 951 920 9456, +63 966 088 7036, +63 918 905 0610.
(`+639519209456` was reformatted with spacing to match the others —
digits unchanged.)

**Visa-specific branch (new):** the function now detects visa inquiries
using the same flag already used by `send_admin_new_inquiry()` for agent
CC routing — `not inquiry.package_id and special_requests.startswith(
'[FOR VISA]')` — and swaps in visa-appropriate copy instead of reusing the
tour-package wording:
- Subject: "We received your visa inquiry for {destination}!" instead of
  "...{destination} inquiry!"
- Intro: "...interest in securing a visa for {destination}!" instead of
  "...interest in our {destination} trip!"
- Expected response items: document checklist, application requirements
  & fees, processing timeline, next steps to file — instead of package/
  pricing language
- "In the meantime": blog + other visa-assisted destinations only — drops
  "Similar package recommendations" and the redundant "Visa requirements
  for {destination}" bullet
- HTML version adds an amber "VISA INQUIRY" badge next to the logo
- Tour-package inquiries are completely unaffected — same wording as
  before in both branches of the `if is_visa` check
- Verified in isolation with a stub `_send()`: visa branch produces the
  visa subject/copy/badge, non-visa branch produces the original copy
  unchanged

### 3. `send_inquiry_confirmed()` — customer confirmation (original wording, restyled)

Restyled to match the receipt email, plus a small teal "✓ Confirmed"
status badge in the header. Not currently branched for visa — same
template for all confirmed inquiries.

## Things to verify

1. **Admin Inquiries search param** — `send_admin_new_inquiry()`'s CTA
   button assumes `?search=<reference_number>` is the correct filter param
   on the admin Inquiries page. If it's named differently, update the
   `admin_link` line in that function.
2. **Existing tests** — any test asserting the exact call signature of the
   mocked `_send()` for any of the three functions (e.g. checking
   positional/keyword args without an `html=` kwarg, the old single-line
   phone format, or the old single subject-line format for visa inquiries
   in `send_inquiry_receipt`) will need updating.
3. **Visa flag fragility** — the `[FOR VISA]` prefix is a string check on a
   free-text field. This isn't a new risk (the admin alert already trusts
   it for CC routing), but worth knowing if that field's format ever
   changes.

## Files changed

- `email_service.py` — `send_admin_new_inquiry()`, `send_inquiry_receipt()`,
  and `send_inquiry_confirmed()` all gained an HTML body;
  `send_inquiry_emails_async()` passes `base_url` through to the admin
  alert; `send_inquiry_receipt()` phone line expanded to six numbers and
  gained a visa-specific content branch.
