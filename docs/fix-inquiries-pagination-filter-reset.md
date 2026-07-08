# Fix: pagination resets "All time" filter to "This month"

## Problem
On the Inquiries admin page, selecting "All time" (or "All types") and
clicking Filter worked correctly on page 1. Clicking through to page 2
silently reset the date filter back to "This month" and lost the type
filter, often landing on "No inquiries found" even though matching
records existed.

## Root cause
`_get_inquiry_filter_params()` in `routes/admin.py` defaults the month
filter to the current month **only when the `month` key is completely
absent from the query string** — this is intentional, so a first-ever
visit to `/admin/inquiries` doesn't try to load every inquiry ever
made.

The status-pill links and the Export Excel button build their URLs
with `url_for(...)`, which always includes every parameter, even when
its value is an empty string (`&month=`). The filter form's hidden
`month`/`year` inputs behave the same way for the same reason. So on
those paths, an explicit "All time" selection (`month=""`) is
correctly distinguished from "no filter set" (`month` key missing
entirely).

The **pagination links** were the one place NOT built this way -
they were hand-assembled with:
```
{% if month_param %}&month={{ month_param }}{% endif %}
```
Jinja's `{% if %}` treats an empty string as falsy, so whenever
"All time" was selected (`month_param == ""`), the `month` param was
dropped from the page-2/page-3/etc. link entirely. On the next
request, the backend saw no `month` key at all, assumed "first visit,"
and re-applied the current-month default - even though the person had
explicitly chosen "All time."

## Fix
`templates/admin/inquiries.html` - replaced the hand-built pagination
href with `url_for('admin.inquiries', page=p, ...)`, matching the
pattern already used by the status pills and Export button. This
always includes every filter param (status, type, search, month, year,
date_from, date_to, sort) in the URL regardless of whether its value
is empty, so "All time" now survives pagination.

**Ctrl+F anchor** (single line changed):
```
Find:    <a href="?page={{ p }}{% if status_filter %}&status=
Replace with a url_for(...) call - see diff below.
```

## Verification
Seeded 37 test inquiries (12 across 2025, 25 in June 2026) via
`scripts/seed_test_inquiries.py`, logged in as admin via a Flask test
client, and replayed the exact scenario:

**Before fix:** `/admin/inquiries?status=&sort=asc&search=&type=&month=&year=&date_from=&date_to=`
(All time) generated a page-2 link of `?page=2&sort=asc` - month/year/
type/status/search all dropped. Following it landed on `All Inquiries
(0)` / "No inquiries found," with the date-mode dropdown reset to
"All types"/no month selected server-side but effectively filtered to
the current month.

**After fix:** the same starting URL now generates a page-2 link of
`/admin/inquiries?page=2&status=&type=&search=&month=&year=&date_from=&date_to=&sort=asc`.
Following it shows `All Inquiries (37)` (correct running total) with
17 of the remaining records rendered (37 total - 20 on page 1), and
the "All time" option still selected in the dropdown.

No migration needed - template-only change.
