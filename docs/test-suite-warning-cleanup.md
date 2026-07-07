# Test suite warning cleanup

## What happened
`pytest` finished green but printed 8 warnings every run, plus an
intermittent 9th one discovered while re-verifying this fix.

## 1. PytestCollectionWarning x2 (Testimonial, TestimonialImage)
Pytest auto-collects any class whose name starts with `Test`. The
`Testimonial` and `TestimonialImage` models aren't test classes, but their
names matched the pattern, so pytest tried to inspect them, couldn't
(they have constructors), and warned about it on every import across 4
test files.

Fix: added `__test__ = False` to both model classes — the standard pytest
convention for telling it "skip this, it's not a test."
- `models/testimonial.py`
- `models/testimonial_image.py`

## 2. LegacyAPIWarning x3
Three test assertions used the SQLAlchemy 1.x style
`Model.query.get(id)`, deprecated in favor of `db.session.get(Model, id)`
in SQLAlchemy 2.0. Still functionally correct, just flagged as legacy.

Fix: switched to `db.session.get(...)`.
- `tests/test_admin_pages.py` (2 occurrences, `TestTestimonialAdminDelete`)
- `tests/test_email_verification.py` (1 occurrence, `test_verify_email_route`
  — also needed a local `from app import db` import added, since the
  function didn't have one)

## 3. PytestUnhandledThreadExceptionWarning (intermittent, found during
   re-verification — not in the original 8, but worth fixing while in here)
Every successful inquiry submission (`plan_my_trip`, `inquire_package`)
calls `send_inquiry_emails_async()`, which spawns a real background
daemon thread to send two emails without blocking the response. Most
tests that POST a valid inquiry don't wait for that thread.

The `app` fixture in `conftest.py` tears down and deletes the per-test
SQLite database file the moment the test function returns. If the
background thread from an inquiry-creation test is still running its
`db.session.get(Inquiry, ...)` query when that teardown fires (whether
in that same test or — since it's an OS thread — bleeding into whatever
test runs next), it raises `sqlite3.OperationalError: no such table` in
the background. This never fails the test itself (the warning gets
attributed to whatever test happens to be executing when pytest's
exception hook catches it, not necessarily the one that started the
thread) — but it's noisy and nondeterministic.

Fix: added an autouse fixture in `conftest.py` that stubs
`email_service.send_inquiry_emails_async` to a no-op for every test by
default, so no real thread gets spawned in the first place. The one test
that specifically needs the real threaded behavior
(`TestInquiryEmailIsAsync::test_plan_my_trip_does_not_block_on_slow_email`)
opts out via a new `real_async_email` marker, registered in `pytest.ini`.
- `tests/conftest.py` — new `_stub_async_inquiry_email` autouse fixture.
- `tests/test_bookings.py` — added `import pytest` and the
  `@pytest.mark.real_async_email` marker on the one test that needs it.
- `pytest.ini` — registered the new marker (required because
  `--strict-markers` is set).

## Result
Verified the thread-race fix isn't just "passed once" — reran the
bookings/inquiries/agents test files 5 times in a row with zero warnings
each time (it was previously flaky, showing up roughly 2 times out of 3).
Full suite: 485 passed, 0 warnings.
