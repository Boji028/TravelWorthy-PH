# Notification badge: '9+' branch was unreachable

## What was wrong
The navbar and mobile-menu badges render
`unread_notification_count if unread_notification_count <= 9 else '9+'`,
but `inject_notifications` in app.py builds that count as
`len(recent_all)` from a query capped at `limit(9)` - deliberately, per
its comment: "Fetch one extra to detect 9+ without a second COUNT query"
(8 are shown in the dropdown, the 9th row only signals there are more).

Since the count can never exceed 9, the `else '9+'` branch never fired:
a user with 20 unread notifications saw a badge of "9" presented as an
exact count, and the one-extra trick did nothing.

## Fix
Changed both badge conditions in templates/base.html to `<= 8`, so the
9th fetched row renders as "9+" as the context processor intended. A
user with exactly 9 unread also sees "9+" - that ambiguity is the
documented trade-off for skipping the COUNT query. The dropdown JS
already handles a "9+" badge when decrementing (parseInt gives 9).

## How it was found
Section-3 review of the new user-notification feature before deploy:
cross-read inject_notifications against the badge templates and noticed
the cap made the overflow branch dead code.
