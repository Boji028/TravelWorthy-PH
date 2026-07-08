# Fix mobile photo gallery overlap and tab bar clipping on package detail

## Problem
On the package detail page at phone widths (tested at iPhone SE, 375px):
- The photo gallery's "Show all photos" button is absolutely
  positioned (`right: 2.5rem; bottom: .75rem`) to sit clear of the
  desktop 2-column layout (1 main image + a 2x2 thumbnail grid). On
  mobile that same 2-column layout just gets squeezed into ~340px, so
  the button ends up overlapping the thumbnail images instead of
  floating clear of them.
- The section tab bar (About / Inclusions / Reviews / Location /
  Fliers) uses the same `2rem` side padding as desktop, leaving only
  ~311px for up to 6 tabs. The last tab or two get clipped, or
  require a horizontal scroll with no visual indication there's more
  to see.

## Fix
Both fixes live entirely inside the mobile-only
`@media (max-width: 768px)` block already in
`templates/packages/detail.html` - nothing here affects tablet
(769-1024px, where the existing 2-column grid has enough room to
look fine) or desktop.

**Gallery**: instead of trying to fit the desktop grid into less
space, collapse to a single full-width hero image on mobile:
- `.photo-grid` goes single-column (`grid-template-columns: 1fr`)
- `.photo-side` (the 2x2 thumbnail grid) is hidden entirely
- `.photo-main` gets full corner rounding (it previously only
  rounded its left corners, expecting the side grid to round the
  right)
- `.show-all-btn` repositioned to `right: 1rem` (previously `2.5rem`,
  which was calculated to clear the now-hidden side grid)

Tapping the hero image or the button still opens the same existing
full-screen photo viewer (`openPhotoViewer()`) - no new viewing logic
needed, just a cleaner entry point into it.

**Tabs**: `.sec-nav-inner` padding reduced from `2rem` to `1rem`, and
`.sec-tab` padding/font-size trimmed slightly (`.7rem 1rem` / `.82rem`
-> `.65rem .65rem` / `.78rem`), giving all 5-6 tabs enough room to sit
with even, visible spacing instead of clipping off-screen.

## Verification
- Brace-balance check on the edited file: 464/464 matched.
- Full test suite: 512/512 passing (pure CSS change inside an
  existing mobile media query, no Python or template logic touched).
- Previewed the before/after gallery and tab layout before
  implementing.

No migration needed - stylesheet-only change within one template.
