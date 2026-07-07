# Mobile pass 2: nav menu redesign + packages filter collapse

**Date:** 2026-07-03

## What changed

### 1. Mobile nav menu rebuilt — `templates/base.html`,
### `static/css/main.css`, `static/js/main.js`

The first-pass restyled dropdown still had problems: the notification
bell floated alone in dead space, the user pill truncated the name
("claudeTEST..."), and CTA buttons were crammed. Replaced with a
dedicated mobile-only menu (`#mobileMenu`) separate from the desktop
`.nav-links` markup, which is now simply hidden on mobile:

- Account strip at top: avatar initial, full name (ellipsized, never
  pill-truncated), notification bell with unread badge (links to My
  Inquiries / admin inquiries — hover dropdowns don't work on touch)
- Logged-out state shows Login / Sign Up buttons in the same strip
- Nav links with Font Awesome icons and active-page highlight pill
- Plan My Trip as full-width amber CTA
- Compact account-action row at bottom (Dashboard for admins, My
  Inquiries, Profile, Logout)
- Hamburger icon swaps to ✕ while open (`navToggleIcon` handling in
  main.js; toggle now targets `#mobileMenu` with `.mm-open` instead
  of `.nav-links`/`.nav-open`)

Desktop nav markup and behavior untouched — `.mobile-menu` is
`display:none` outside the 768px media query.

### 2. Packages list filters collapsed to one row on mobile —
### `templates/packages/list.html`

The sticky toolbar (continent tabs + type pills + search + apply) was
4+ wrapped rows on a 375px screen, eating so much height that only
one package card was visible at a time. Now on mobile it collapses
to a single row: destination search + a "Filters" button (amber dot
indicator when any filter is active). Tapping expands the existing
continent chips, type pills, and Apply/Clear buttons in place —
reusing the same DOM elements, so all existing AJAX filter JS keeps
working with zero changes. Additional touch fix: continent
sub-menus (countries) were hover-only dropdowns, unusable on touch;
on mobile the first tap on a continent now reveals its country list
inline, second tap (or a country tap) navigates.

Desktop toolbar unchanged — all rules inside a 768px media query.

## Verification

Both views checked at iPhone SE width and desktop after each change:
desktop rendering identical, mobile behavior as designed.
