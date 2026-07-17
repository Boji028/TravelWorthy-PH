# Remove nav/footer width cap for wide desktop/laptop screens

**Date:** 2026-07-17

## What changed

`.nav-inner`, `.footer-inner`, and `.footer-bottom` in
`static/css/main.css` all had `max-width: 1280px; margin: 0 auto;` -
a standard centered-container pattern. On screens wider than
~1344px (1280px + the 2rem/32px horizontal padding on each side),
this created visible empty margins on both sides of the header and
footer. Boji's own device is narrow enough that the cap never
engaged, so the nav looked edge-to-edge for him; on a friend's wider
laptop screen the gap was clearly visible, which read as "doesn't
fit right."

Changed all three to `max-width: none`, so the row always spans the
full available width (still respecting the existing 2rem padding)
regardless of screen size.

## Why this is safe (checked before changing)

- **Nav**: `.nav-links` already has its own internal spacer
  (`<li style="flex:1"></li>` between "Plan My Trip" and the
  notification bell / account controls). That spacer absorbs all the
  extra width on a wide screen - individual links don't spread apart,
  the browsing links stay clustered near the logo and account actions
  stay clustered on the right, exactly matching the reference
  screenshot. This is the same layout pattern as GitHub, Amazon, etc.
- **Footer**: `.footer-inner` is a proportional grid
  (`1.8fr 1fr 1fr`) and `.footer-bottom` is `justify-content:
  space-between` - both scale cleanly with extra width, no broken
  layout.
- **Mobile/tablet unaffected**: the hamburger nav already takes over
  at `≤1024px` (a separate, unrelated media query), so this change
  only has any visible effect above that width - real desktop/laptop
  screens only.
- **`.container`** (the same 1280px pattern, generic utility class)
  was deliberately left alone - it's used on only two minor auth
  pages and wasn't part of what was reported, so out of scope here.

## Tests

CSS-only change; ran `test_public_pages.py` and `test_packages_public.py`
(30 tests) as a sanity check that nothing broke - all passed, as
expected for a change with no template/route logic involved.
