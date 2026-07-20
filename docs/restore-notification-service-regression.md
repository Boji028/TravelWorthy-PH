# Restore notification_service.py functions dropped by an unrelated commit

## What was wrong
Commit `ccc94bd` ("feat: branded reply feature for contact messages in admin
panel") accidentally reverted `notification_service.py` down to a single
function (`notify_inquiry_status_change`), silently deleting
`notify_inquiry_created`, `notify_admins_new_inquiry`,
`notify_admins_inquiries_expiring`, `notify_users_new_package`, and
`notify_users_new_visa` — none of which have anything to do with contact
messages. The commit's actual diff (`git show ccc94bd -- notification_service.py`)
confirms this was an accidental stray write, not an intentional change.

Every remaining caller of the missing names hit `ImportError` at runtime:
- `routes/bookings.py` (`plan_my_trip`, `inquire_package`) — wrapped in a
  swallowing `try/except`, so every new inquiry submission silently
  produced zero in-app notifications for both the customer and admins.
- `routes/admin.py` (`add_package`, `visa_add`) — also swallowed, so the
  "notify users of new package/visa" feature was completely inert.
- `inquiry_cleanup_service.py::notify_admins_of_expiring_inquiries` — no
  surrounding try/except; propagated up through
  `scripts/run_inquiry_cleanup.py`, which logged an error and exited 1 on
  every scheduled run. The admin "inquiries about to be auto-deleted"
  warning never fired.
- `tests/test_notifications.py` and `tests/test_inquiry_cleanup.py`
  imported these names directly and failed at collection/execution
  (13 + 4 failing tests respectively in the audit baseline).

## Fix
Restored `notification_service.py` verbatim from
`git show ccc94bd~1:notification_service.py` (the last known-good version,
immediately before the regression) rather than rewriting the functions from
scratch, since the original implementation already matched what the
existing tests and call sites expect.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding B1).
Flagged by grepping for the missing function names across the repo and
confirming an `ImportError` via a direct `python -c "import
notification_service"` check, then traced to the exact regressing commit
with `git log --oneline -- notification_service.py`.

## Tests
No new test needed — the existing `tests/test_notifications.py` (13 tests)
and `tests/test_inquiry_cleanup.py::TestNotifyAdminsOfExpiringInquiries`
(4 tests) already covered this behavior and were failing before the fix.
All 63 tests across `test_notifications.py`, `test_inquiry_cleanup.py`, and
`test_bookings.py` pass after the restore.
