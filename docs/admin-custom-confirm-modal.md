# Replace native browser confirm() with a custom modal, sitewide

## What happened
Every destructive action across the admin panel (delete, remove photo,
bulk actions, toggle admin access, etc.) used the native browser
`confirm()` dialog — the plain "192.168.68.103:5000 says ..." box with
generic OK/Cancel buttons, completely mismatched with the rest of the
redesigned admin UI. Found 19 call sites across 11 templates.

## Decision
Previewed a custom-styled modal (rounded card, icon badge, Cancel/Delete
buttons matching the existing `.btn-ghost`/`.btn-danger` classes) before
implementing. Built it once in `base_admin.html` (which every admin
template extends) instead of duplicating markup per page.

## Architecture
- `window.adminConfirm(message, opts)` — async, Promise-based drop-in
  replacement for `window.confirm()`. `opts.danger` (default `true`)
  switches between a red trash icon / "Delete" button and a neutral teal
  circle-question icon / amber "Confirm" button for non-destructive
  confirmations (e.g. granting admin access).
- A single document-level delegated `submit` listener intercepts any
  `<form data-confirm="message">`, shows the modal, and on confirmation
  re-submits via `form.requestSubmit()` (guarded against re-entry with a
  one-shot `__confirmBypass` flag) — so most of the 19 sites needed zero
  custom JS, just swapping `onsubmit="return confirm('...')"` for
  `data-confirm="..."`.
- `data-confirm-danger="false"` opts a form into the neutral style.
- Cases with a dynamic, runtime-computed message (bulk-delete count,
  bulk package action) or that were already inside a JS function instead
  of a form submit call `await adminConfirm(...)` directly.

## Two pre-existing dead confirmations found and fixed along the way
`edit_package.html` (photo + flier removal) and `edit_visa.html` (PDF
removal) triggered their hidden forms via `form.submit()` — which, per
the DOM spec, does **not** fire the `submit` event or run `onsubmit`.
Their `confirm()` calls never actually ran; clicking Remove Photo/Flier/PDF
removed the file immediately with no prompt at all. Fixed by switching
those three buttons to `form.requestSubmit()` (which does fire the event)
as part of converting them to the new pattern. Same root cause was found
in `contact_messages.html`'s bulk-delete button.

The flier-removal form (`edit_package.html`) additionally had no
confirmation prompt at all, even a dead one — added one for consistency
with the photo-removal form right next to it.

## Files changed
- `templates/admin/base_admin.html` — new modal markup, CSS, and the
  `adminConfirm()` / delegated-submit JS, available to every admin page.
- `static/css/main.css` — (no changes needed; modal CSS lives in
  base_admin.html's own style block since it's admin-only)
- `templates/admin/agents.html` — dynamic Jinja message via `data-confirm`
  (replaced a `| tojson` JS-string-literal embed, which is also safer:
  the old version could have produced broken JS if an agent name ever
  contained a quote — HTML-attribute escaping doesn't have that problem).
- `templates/admin/blog.html`, `continents.html`, `countries.html`,
  `inquiries.html`, `visa.html`, `packages.html` (single delete),
  `contact_messages.html` (single delete), `edit_blog.html` (photo
  remove), `testimonials.html` (remove-photos form) — static-message
  `data-confirm` conversions.
- `templates/admin/users.html` — two dynamic Jinja messages
  (admin-toggle uses `data-confirm-danger="false"`; delete uses the
  default danger style). Also fixes the same raw-quote-in-JS-string risk
  as agents.html, since `user.name` was interpolated directly into a JS
  string literal before.
- `templates/admin/packages.html` — `bulkAction()` made `async`, both
  dynamic-count confirms now use `adminConfirm()` (delete = danger,
  deactivate = neutral, since deactivating is reversible).
- `templates/admin/contact_messages.html` — bulk-delete button now calls
  a small `confirmBulkDeleteMessages()` helper that computes the live
  checkbox count, awaits `adminConfirm()`, then `requestSubmit()`s.
- `templates/admin/edit_package.html` — photo-remove and flier-remove
  buttons switched to `requestSubmit()` + `data-confirm`; the now-dead
  `addEventListener('submit', ...)` script removed; `deleteGalleryImage()`
  (already async) now awaits `adminConfirm()`.
- `templates/admin/edit_visa.html` — same `requestSubmit()` + `data-confirm`
  fix for PDF removal, dead listener script removed.

## Verification
- Full suite: 485 passed (route tests POST directly and never touch the
  client-side confirm flow, so this confirms no template/Jinja breakage,
  not the JS behavior itself).
- Rendered `agents.html` and `users.html` with names containing
  apostrophes, ampersands, and angle brackets to confirm
  `data-confirm="{{ ... }}"` escapes correctly for safe HTML-attribute
  embedding (it does — `&#39;`, `&amp;`, `&lt;`, `&gt;`).
- Syntax-checked every modified `<script>` block with `node --check`.
- Manually swept the entire `templates/admin/` directory for `confirm(`
  — zero native calls remain.

## Hotfix: modal showing on every page load, Cancel not working
Shortly after delivery, the modal turned out to be visible on every
admin page (Dashboard included) immediately on load, with no message
text, and Cancel appeared to do nothing.

Root cause: `.admin-confirm-overlay { display: flex; ... }` in CSS and
the element's `hidden` attribute have equal selector specificity, so the
author stylesheet's `display: flex` was winning over the browser's
built-in `[hidden] { display: none }` rule — the overlay was visually
showing at all times regardless of the `hidden` attribute's actual
state. Cancel was working correctly in JS (toggling the attribute,
resolving the promise) but had zero visual effect because of this.

Fix: added an explicit `.admin-confirm-overlay[hidden] { display: none; }`
rule, which (being more specific than the bare class selector) correctly
overrides `display: flex` whenever `hidden` is present.

Verified by rendering `/admin/` (Dashboard) directly through Flask's test
client and confirming the new rule is present in the response HTML, plus
a full test-suite run (485 passed).

## Follow-up: Inquiries delete now AJAX (no full page reload)
After the hotfix above, deleting an inquiry still caused a full page
reload — not a new issue, this was the existing behavior even before
today's changes (the delete route does a standard server-side redirect,
and unlike the page's search/filter bar, individual row actions were
never wired into the existing AJAX refresh mechanism).

Since the rest of the admin panel has been getting this polish today,
converted Inquiries delete specifically to match: the delete form's
`data-confirm` was removed (now handled explicitly inside the page's
own `inquiriesApp` submit listener instead of the generic site-wide
handler, since it needs custom post-confirmation behavior). On confirm,
the row is deleted via `fetch()` and the table refreshes in place via
the page's existing `loadInquiries()` function — the same mechanism
already used for filtering — instead of a full browser navigation.

No backend changes; `delete_inquiry` still does its normal
flash+redirect, which is harmless when called via fetch and still works
correctly as a plain form submit if JS is unavailable (progressive
enhancement preserved).

Verified end-to-end with CSRF protection enabled: logged in, confirmed
the delete form has the new class and no `data-confirm`, performed the
delete via a simulated fetch (POST + redirect-follow), confirmed the
inquiry was actually removed from the database, and confirmed the
follow-up refresh request returns the `inquiriesApp` fragment correctly.
Full suite: 485 passed.

Note: this same "full page reload on delete" pattern likely exists on
the other admin list pages too (Packages, Continents, Countries, Users,
Blog, Visa, Testimonials, Contact Messages, Agents) — out of scope here
since this was specifically about Inquiries, but worth a follow-up if
wanted later.
