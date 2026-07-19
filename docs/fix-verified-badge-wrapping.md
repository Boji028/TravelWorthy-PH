# Fix "Verified Agency" badge splitting apart on narrow screens

**Date:** 2026-07-19

## Root cause

```html
<div class="host-name">Hosted by Travel Worthy PH <span class="verified-badge">⭐ Verified Agency</span></div>
```

`.verified-badge` had no `white-space: nowrap` and defaulted to
`display: inline`. On a narrow screen, once "Hosted by Travel Worthy
PH" plus the badge stopped fitting on one line, the browser was free
to wrap *inside* the badge's own content too, breaking the line right
between the star emoji and "Verified Agency". Since `border-radius`
and `border` on an inline element render per line-box (not as one
shape around the whole wrapped content), that split rendered as two
disconnected fragments - a small circular sliver around the star, and
a separate pill around the text - which read as the badge being cut
off.

## Fix

Added `white-space: nowrap` (plus `display: inline-flex` and a small
`gap` for cleaner star/text alignment) so the badge's content is
always treated as one unbreakable unit - it now moves to the next
line as a whole if it doesn't fit, instead of splitting internally.

Checked for the same emoji-plus-text-in-one-span pattern elsewhere:
found `templates/blog/list.html`'s `.featured-badge` ("✦ Featured").
Lower risk there since it's `position: absolute` over a thumbnail
image rather than competing for space with a long preceding text
string, but added the same `white-space: nowrap` defensively since
it's a zero-risk, one-line addition.

## Tests

CSS-only change, no template logic touched. Ran
`test_packages_detail.py` and `test_admin_blog.py` (32 tests) to
confirm both touched templates still render. Full suite: 559 passed,
2 pre-existing warnings unrelated to this change.
