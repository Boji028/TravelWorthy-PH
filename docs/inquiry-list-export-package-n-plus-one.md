# Eager-load package on admin inquiries list and xlsx export

## Problem
Both the admin inquiries list (`admin/inquiries.html` renders
`inq.package.title` in the expanded detail row) and the xlsx export
(`export_inquiries` writes `inq.package.title` per row) read the
package relationship without eager loading, firing one lazy-load
SELECT per inquiry. The list is paginated at 20/page (bounded, ~21
queries per page load instead of a handful); the export is unbounded —
exporting a busy month of N inquiries meant N+1 queries.

Same bug class as testimonial-review-selectinload-n-plus-one.md; the
dashboard's `recent_inquiries` already had the joinedload fix, these
two call sites were missed.

## Fix
`routes/admin.py`: added `.options(joinedload(Inquiry.package))` to the
paginated query in `inquiries()` and to the base query in
`export_inquiries()`. joinedload (not selectinload) since it's a
many-to-one to a single row — one LEFT JOIN, no second statement.
The count query in `inquiries()` deliberately stays on the plain
`base_query` (it uses `with_entities`, where loader options don't apply).

Also corrected a stale comment in `users()` claiming "Inquiry has no
user_id FK" — it does (nullable, guests submit with user_id=None);
matching by email is still right because it also counts a user's
pre-registration inquiries.

## Verification
No behavior change — existing list/export tests
(test_admin_inquiries.py) pass unchanged.
