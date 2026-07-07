# Inquiry performance fixes

## What changed

### routes/admin.py — pill counts
Replaced four separate COUNT queries (one per status) with a single query
using conditional SUM so the database makes one pass instead of four.
Previous approach ran: SELECT COUNT(*) WHERE status='new', SELECT COUNT(*)
WHERE status='contacted', etc. — one round trip per status pill.

### routes/admin.py — default date filter
Admin inquiries page now defaults to the current month when no filters are
active. Prevents loading all-time inquiries on every fresh page open, which
matters as the table grows. Any explicit filter (search, status, type, date
range) overrides the default so admin can still view all-time data freely.

## Files changed
- routes/admin.py