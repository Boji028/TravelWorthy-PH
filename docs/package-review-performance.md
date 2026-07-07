# Package review performance fixes

## What changed

### routes/packages.py
- Replaced Python-side avg_rating calculation (`sum(r.rating for r in reviews)`)
  with a single SQL `func.avg()` query so the database does the work instead
  of loading all review rows into memory just to average them.
- Added `func` to sqlalchemy imports.

### models/package_review.py
- Added `index=True` to `package_id` — speeds up filtering reviews by package
  on the detail page, which is the most frequent query on this table.
- Added `index=True` to `created_at` — speeds up the `ORDER BY created_at DESC`
  sort on the same query.

## Migration required
Run after applying model changes:
  flask db migrate -m "Add indexes to package_reviews package_id and created_at"
  flask db upgrade

## Why
At scale, `.all()` on a large reviews table loads every row into Python memory
before averaging. SQL avg() does it in one pass at the database level.
Without indexes, filtering and sorting package_reviews does a full table scan
on every package detail page load.

## Files changed
- routes/packages.py
- models/package_review.py