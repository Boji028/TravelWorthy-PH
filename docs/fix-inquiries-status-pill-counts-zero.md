# Fix: status pill counts (All/New/Contacted/Confirmed/Closed) show 0 with no filters active

## Problem
On the Inquiries admin page, the status pills at the top ("All (0)",
"New (0)", "Contacted (0)", "Confirmed (0)", "Closed (0)") always
showed 0 whenever "All time" + "All types" were selected with no
search term - even though the list below correctly showed real
records ("Closed Inquiries (15)").

## Root cause
`routes/admin.py`, inside `inquiries()`:

```python
count_rows = (
    db.session.query(func.count().label("total"), ...)
    .filter(base_query.whereclause)
    .one()
)
```

`base_query.whereclause` is SQLAlchemy's way of exposing whatever
WHERE conditions `_apply_inquiry_filters()` built up via `.filter()`
calls. When *no* filters are active (All time, All types, no search),
`_apply_inquiry_filters()` never calls `.filter()` at all, so
`base_query.whereclause` is `None`.

Passing `None` into `.filter(None)` doesn't mean "no filter" - it
builds a WHERE clause of literal `NULL`. In SQL, `WHERE NULL` is
neither true nor false for any row (it's "unknown"), which the
database treats as false and excludes every row. That's why
`COUNT(*)` came back as `0` and every `SUM(CASE ...)` came back as
`NULL` (no rows to sum) - reproduced directly:

```
count_rows: (0, None, None, None, None)
```

while the actual filtered list further down the page uses a
completely separate, correctly-built query (`base_query.filter_by(status=...).paginate(...)`),
which is why the list itself showed the right records the whole time.

This only shows up when *no* filter is active, which is the single
most common view of the page (opening it fresh, clearing filters,
picking "All time") - hence "why is it always 0."

## Fix
Reuse `base_query` directly via `.with_entities(...)` instead of
extracting its `.whereclause` and re-applying it to a brand-new query.
`with_entities()` swaps the SELECT columns on the *same* query object
- filters and all - so it works identically whether zero, one, or
several filters are active, with no `None`-whereclause edge case:

```python
count_rows = base_query.with_entities(
    func.count().label("total"),
    func.sum(case((Inquiry.status == "new", 1), else_=0)).label("new"),
    func.sum(case((Inquiry.status == "contacted", 1), else_=0)).label("contacted"),
    func.sum(case((Inquiry.status == "confirmed", 1), else_=0)).label("confirmed"),
    func.sum(case((Inquiry.status == "closed", 1), else_=0)).label("closed"),
).one()
```

## Test coverage added
`tests/test_admin_lists.py::TestInquiriesList::test_status_pill_counts_with_no_filters_active`
- creates 4 inquiries across 3 statuses, requests the page with every
filter param explicitly empty (`month=&year=&date_from=&date_to=&type=&search=`,
matching what the "All time" dropdown actually submits), and asserts
the real pill counts appear ("All (4)", "New (1)", "Contacted (1)",
"Closed (2)").

Confirmed this test fails against the old `.filter(base_query.whereclause)`
code (asserts "All (4)" but gets "All (0)") and passes against the fix.
None of the existing tests caught this because they either never
touch the endpoint with all filters explicitly cleared, or hit it with
no query string at all - which triggers a different code path (the
current-month default) that happens to keep `whereclause` non-`None`.

## Verification
Full suite: 512/512 passing (511 existing + 1 new regression test).

No migration needed - route logic + test only.
