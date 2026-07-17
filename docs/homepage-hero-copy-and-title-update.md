# Homepage hero copy and tab title update

**Date:** 2026-07-16

## What changed

Boss-requested copy change to `templates/main/home.html`:

- Hero headline: "Your Travel made / worth it." → "Your travels, / Made
  worth it" — line break moved after "Your travels,", and only "worth
  it" keeps the teal italic color (`<em>`); "Made" is now plain white.
  Kept the existing word-by-word fade-in animation structure (three
  staggered `.w` spans) so the entrance effect is unaffected.
- Browser tab title simplified to "Travel Worthy PH" only. This matches
  `base.html`'s default title block exactly, so the per-page override
  in `home.html` was removed entirely rather than left as a duplicate.

No backend/route changes. No tests reference the hero copy or title
text, so nothing else needed updating; `tests/test_public_pages.py`
(20 tests) re-run clean after both edits.
