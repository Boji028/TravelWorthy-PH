# Fix card grids overflowing/cutting off on narrow phones

**Date:** 2026-07-19

## Root cause

`grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))` sets a
**hard minimum** of 320px per column. If the actual available width
(viewport minus the page's side padding) is narrower than that
minimum, the grid track still refuses to shrink below 320px — it
overflows the visible viewport instead, cutting content off the edge
of the screen rather than wrapping or shrinking to fit.

On `packages/list.html` specifically: `.packages-wrap` has
`padding: 0 2rem` (32px each side, 64px total). An iPhone 12's 390px
viewport leaves only 326px available - a 6px margin over the 320px
floor. That's razor-thin: any small difference between rendering
engines, or literally any phone with a narrower screen (iPhone SE at
375px leaves only 311px, well under 320px), pushes it into overflow.
Chrome DevTools' device emulation and real Safari can legitimately
compute this a few pixels differently, which is exactly why it looked
fine in the emulator and cut off on the real device.

## Fix

Wrapped every fixed-pixel `minmax()` minimum in `min(Npx, 100%)`:

```css
/* before */
grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
/* after */
grid-template-columns: repeat(auto-fill, minmax(min(320px, 100%), 1fr));
```

`min(320px, 100%)` uses whichever is smaller - on any viewport wide
enough to fit a 320px column, `100%` is bigger and `min()` just
resolves to `320px` as before (zero visual change on tablet/desktop).
On a viewport too narrow for that, `100%` becomes the smaller value,
so the column shrinks to fit the container exactly instead of
overflowing. This is the standard fix for this well-known CSS Grid
trap, and it degrades gracefully with no fallback needed - `min()` has
been supported in all major browsers, Safari included, since 2020.

Applied everywhere this same pattern was copy-pasted, not just the
packages grid that was reported:

- `templates/packages/list.html` - `.packages-grid`, 320px → the
  actual reported bug
- `templates/blog/list.html` - stories grid, 300px
- `templates/main/home.html` - `.tw-tiles` (220px) and `.tw-cards`
  (280px)
- `templates/packages/visa.html` - `#visa-grid`, 220px

Left `templates/admin/dashboard.html`'s `.stats-grid` alone - it
already uses `minmax(0, 1fr)`, which has no overflow risk in the
first place.

## Tests

CSS-only change, no template logic touched. Ran
`test_packages_public.py`, `test_public_pages.py`, `test_admin_visa.py`,
and `test_admin_blog.py` (56 tests) as a sanity check that every
touched template still renders - all passed. Full suite: 557 passed,
2 pre-existing warnings unrelated to this change.
