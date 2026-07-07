# Add reference number to inquiry search; lock destination field

## What changed

### routes/admin.py
- Added Inquiry.reference_number to the or_() search filter in the inquiry
  filter helper so admins can search by reference number (e.g. INQ-7083E6)
  in addition to name and email.

## Files changed
- routes/admin.py — reference_number added to search or_() filter
- templates/admin/inquiries.html — search placeholder updated to mention
  reference number
- templates/packages/detail.html — Travel Destination field in the package
  inquiry modal made readonly, pre-filled from package.destination, red
  asterisk and required attribute removed since it is no longer user-editable