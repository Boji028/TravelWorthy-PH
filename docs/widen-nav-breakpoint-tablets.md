# Widen nav breakpoint from 768px to 1024px so tablets get the mobile menu

## Problem
At tablet widths like iPad Air (820px, portrait), the site was still
showing the full desktop nav (logo, 7 text links, "Plan My Trip"
button, notification bell, account dropdown) instead of the hamburger
menu, because the breakpoint that switches between them was
`max-width: 768px` - and 820px is above that. The full nav's items
are all `white-space: nowrap` with no wrapping fallback, so at
tablet widths they were cramped with very little breathing room and
small touch targets for a touch device.

## Fix
`static/css/main.css`: widened the nav's media query from
`max-width: 768px` to `max-width: 1024px`. This covers:
- All phones (portrait and landscape)
- iPad Mini (768), iPad Air (820), standard iPad (810), iPad Pro 11"
  portrait (834) - all now get the mobile menu
- iPad Pro 12.9" portrait (1024) - right at the new boundary, gets
  the mobile menu
- Desktop/laptop (>1024px) keeps the full nav, where there's actually
  room for it

The same media query block also contained unrelated flash-message and
footer rules (`.flash-wrap`, `.flash`, `.footer-inner`,
`.footer-bottom`). Those were split into their own separate
`@media (max-width: 768px)` block so they keep their original
breakpoint - widening those wasn't part of what we agreed on, and
footer/flash behavior at tablet widths is a separate decision.

`static/js/main.js`: the dropdown tap-to-toggle handler had its own
hardcoded `window.innerWidth <= 768` check, gating the notification
bell and account dropdowns (the only two elements using
`.dropdown-toggle` anywhere in the codebase - confirmed via a
sitewide search). Since those dropdowns live inside `.nav-links`,
which is now hidden below 1024px instead of 768px, updated this
threshold to `1024` to match. Harmless either way (the dropdowns
aren't reachable in the 769-1024px range regardless, since their
parent is `display: none` there), but keeps the two thresholds in
sync instead of silently drifting apart.

## Scope note
Five other templates still have their own `max-width: 768px` media
queries for page-specific layout (packages list/detail, blog
list/detail, admin inquiries). Those are unrelated to the header nav
and were intentionally left alone - a broader pass to consolidate all
of the site's ~8 scattered breakpoint values onto one consistent
scale is a separate follow-up, not part of this fix.

## Verification
- Brace-balance check on the edited stylesheet: 148 open / 148 close,
  matched.
- Full test suite: 512/512 passing (pure CSS/JS change, no Python
  touched).
- Sitewide search confirmed no other file references the nav's old
  768px threshold.
- Previewed the before/after nav behavior across phone (375),
  iPad Mini (768), iPad Air (820), iPad Pro (1024), and desktop (1280)
  reference widths before implementing.

No migration needed - static asset changes only.
