# Auto-delete inquiries after 3 months, with an admin warning first

## What this does
- Inquiries older than 3 months (90 days) get deleted automatically, any
  status — confirmed per your answer, no exceptions for still-active ones.
- Before that happens, admins get an in-app notification (the existing
  bell icon) once an inquiry enters its final 7 days: "N inquiries will
  be auto-deleted in the next 7 days. Download them from Inquiries before
  they're removed." It links straight to the admin Inquiries page.
- If an inquiry was already exported (via the existing Inquiries export
  button) within the last 7 days, it's excluded from that count and won't
  keep triggering reminders — per your "auto detect if downloaded" ask.
- The reminder re-checks and re-sends roughly every 2 days (not every
  single day) as long as something's still at risk, landing at 3-4
  times/week, matching "at least 3 times a week" without being a daily
  nag.
- Runs once a day via Windows Task Scheduler, the same way your backups
  already do — recommended over an in-process background thread since
  that only runs while `python run.py` happens to be up, and can
  double-fire under the dev server's auto-reloader.

## New files
- `inquiry_cleanup_service.py` — the two core functions:
  `notify_admins_of_expiring_inquiries()` and `delete_expired_inquiries()`.
  Deletion goes through `db.session.delete()` one inquiry at a time (not
  a bulk `.delete()` query), so InquiryNotification's existing
  `cascade="all, delete-orphan"` relationship actually fires instead of
  leaving orphaned notification rows or hitting a foreign key error.
- `scripts/run_inquiry_cleanup.py` — standalone entrypoint (mirrors
  `scripts/run_backup.py`): warns first, then deletes, in that order, so
  nothing gets removed without at least one reminder cycle.
- `scripts/run_inquiry_cleanup.bat` +
  `scripts/setup_inquiry_cleanup_scheduler.ps1` /`.bat` — mirror the
  existing backup scheduler setup exactly (same Task Scheduler
  registration pattern), registers a new daily task called
  "Travel Agency Inquiry Cleanup" at 3:00 AM by default (an hour after
  the 2:00 AM backup).
- `tests/test_inquiry_cleanup.py` — 9 tests.

## Changed files
- `models/inquiry.py` — new `last_exported_at` (nullable DateTime,
  indexed) column, stamped whenever an inquiry is included in an export.
- `models/inquiry_notification.py` — `inquiry_id` is now nullable, so a
  system-wide reminder ("N inquiries...") can exist without being tied to
  one specific inquiry. Docstring updated to explain why.
- `templates/base.html` — the notification dropdown did
  `n.inquiry.user_id == current_user.id`, which would crash on a
  system-wide notification (`n.inquiry` is None). Changed to
  `n.inquiry and n.inquiry.user_id == ...` — falls through to the
  existing "link to admin.inquiries" branch, which is exactly right for
  this new notification type too.
- `routes/admin.py::export_inquiries` — after building the (filtered)
  export list, bulk-updates `last_exported_at = now()` for every inquiry
  included, before generating the Excel file.
- `notification_service.py` — new `notify_admins_inquiries_expiring(count)`,
  same shape as the existing `notify_admins_new_inquiry`, just with
  `inquiry_id=None` and a count-based message.
- New migration `a7c3f9e2b1d4` (chains off your current head
  `c2551e8ab7aa`) — adds the column and the nullable change.

## Design notes
- 3 months = 90 days flat, not calendar months, for simplicity.
- Deletion is ORM-level (`db.session.delete()` per row), not a bulk
  `query.delete()` — bulk deletes bypass SQLAlchemy's relationship
  cascade entirely, which is exactly the kind of thing your `CLAUDE.md`
  "Known Pitfalls" note already warns about for Inquiry/Notification.
- All datetime comparisons follow the codebase's existing pattern: SQL
  filters use aware `datetime.now(timezone.utc)` directly (already proven
  fine elsewhere — see `routes/admin.py`'s dashboard 7-day trend query),
  and the one Python-side comparison (checking when the last reminder was
  sent) explicitly normalizes tzinfo the same way
  `PasswordResetToken._aware()` / `EmailVerificationToken._aware()` do.

## Verification
- New tests (9): deletion of an expired inquiry and its cascade to
  notifications, a recent inquiry surviving regardless of status, the
  reminder firing for an at-risk un-exported inquiry, the reminder being
  skipped for one exported in the last week, the reminder being skipped
  outside the warning window, the throttle preventing back-to-back
  duplicate reminders, the export route stamping `last_exported_at`, and
  the admin dashboard rendering correctly with a system-wide notification
  present (the base.html crash-guard).
- Migration tested both directions against a database seeded to match
  your actual current schema (stamped at `c2551e8ab7aa`, not a fresh
  from-scratch replay) — upgrade adds the column and nullable change
  correctly, downgrade removes them cleanly.
- Full suite: 531/531 passing (522 existing + 9 new).

## Before you apply this
This permanently deletes inquiry data. Test it against a copy of your
database first, or at minimum run `scripts/run_inquiry_cleanup.py`
manually once and check the output before wiring up the scheduled task.

## Still needed after applying
1. `flask db migrate` isn't needed (migration file is already written) —
   just `flask db upgrade`.
2. Run `scripts/setup_inquiry_cleanup_scheduler.bat` as Administrator
   once, same as you did for backups.
