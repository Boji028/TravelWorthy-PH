# Inquiry performance notes

## Current state (no changes needed yet)

The Inquiry model already has indexes on the most queried columns:
- reference_number (unique, indexed)
- email (indexed)
- status (indexed)
- created_at (indexed)
- user_id (indexed)

Pagination is in place on the admin inquiries page.
AJAX in-place filtering avoids full page reloads.

## Known future pressure points

### 1. ilike search with leading wildcard
The admin search uses `ilike("%search%")` on name, email, and reference_number.
Leading wildcards bypass B-tree indexes and do a full table scan.
Fine at 1,000-5,000 rows. May slow down past 20,000+ rows.
Fix when it becomes noticeable: add PostgreSQL GIN/trigram index on those columns.

### 2. Pill count queries
Four separate COUNT queries run on every admin inquiries page load
(one per status: new, contacted, confirmed, closed).
These scan the full table regardless of pagination.
Fix when noticeable: cache counts with a short TTL (e.g. 60 seconds).

### 3. No default date filter
The admin inquiries page loads all-time inquiries by default.
At very high volume, setting a default date range (e.g. last 3 months)
would reduce the default query size significantly.
Fix when noticeable: add a default date_from fallback in the route.

## Action required
None right now. Revisit if the admin reports slowness on the inquiries page.