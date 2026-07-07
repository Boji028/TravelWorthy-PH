# Review edit feature + form-action bug fix

## What happened
While discussing whether to remove the one-review-per-package-per-user limit,
found that the review submission form on the package detail page was posting
to `bookings.inquire_package` instead of `packages.submit_review` — a
copy-paste leftover from the inquiry form. This meant reviews could never
actually be created through the live site UI. It went uncaught because the
test suite calls the `/packages/<id>/review` route directly, bypassing the
template entirely.

## Decision
Kept the one-review-per-user-per-package restriction (DB UniqueConstraint +
app check) — it's standard practice and prevents rating manipulation. Added
the ability to edit an existing review instead, since that's the legitimate
need behind wanting to remove the restriction (e.g. updating a typo or
revising a rating).

## Changes
- `routes/packages.py`
  - `package_detail()` now passes the user's own `PackageReview` object
    (`user_review`) to the template, not just a boolean.
  - Added `edit_review()` route (`POST /packages/<id>/review/edit`) — updates
    rating/message on the existing review, same validation as `submit_review`.
- `templates/packages/detail.html`
  - Fixed the review form's `action` to point at `packages.submit_review`.
  - Replaced the dead-end "already reviewed" message with an editable form
    pre-filled with the user's existing rating/message, posting to
    `packages.edit_review`.
  - Star-rating JS now initializes from the rendered `rating-input` value
    instead of hardcoding 5, so the edit form shows the correct stars on load.
    Also calls `updateReviewChar()` on load so the char counter reflects
    pre-filled text.
- `tests/test_admin_packages.py` — added `TestPackageReviewEdit` (login
  required, 404 with no existing review, valid update, invalid rating/empty
  message leave the review unchanged).
- `tests/test_packages_detail.py` — added a regression test asserting the
  rendered form action is `packages.submit_review`, and a test asserting the
  edit form renders with the user's existing review when one exists.

## Result
Full suite: 481 passed (474 existing + 7 new).
