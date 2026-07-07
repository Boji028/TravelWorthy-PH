# Fix: visa inquiries lost customer's own message on tracking page

**Date:** 2026-07-03

## What was found

During a full live QA pass (Claude Code exercising the running dev
server against real PostgreSQL, not just pytest), one real bug turned
up: `templates/main/inquiry_status.html` hid the entire "Your notes"
section whenever `special_requests` contained the internal `[FOR
VISA]` tag, instead of stripping just that tag and showing the rest
of the customer's actual message.

**Impact:** a customer submitting a visa inquiry through the visa
assistant form could type a real question (e.g. "Need help with Japan
visa for my kids too") and then never see their own message again on
`/inquiry/<reference_number>`. Regular package/trip inquiries were
unaffected — this only hit the visa-inquiry path.

## Fix

`templates/main/inquiry_status.html` — strip the `[FOR VISA]` prefix
from `special_requests` before rendering, rather than hiding the
whole notes block when the tag is present.

## Verification

Re-tested live against both:
- A visa inquiry — customer's note now displays correctly (tag
  stripped, message shown)
- A regular package inquiry — unaffected, notes display as before

## Origin

Not a regression from the recent OAuth, register.html redesign, or
file reorganization work — this predates all of that. Looks like an
oversight from when the `[FOR VISA]` branching was originally added
to the admin/email side (see prior activity log entries on the
notification system and agent-based inquiry routing) without the
customer-facing tracking template being updated to match.

## Related note from the same QA pass

Testing surfaced that packages/visa records in the dev database have
real assigned agents, so submitting test inquiries against them
triggers real SMTP sends to those agents' actual inboxes (not just to
disposable test addresses). Worth keeping in mind for future live QA
passes — either test against a package with no agent assigned, or use
a dedicated test agent record, to avoid emailing real inboxes during
testing.
