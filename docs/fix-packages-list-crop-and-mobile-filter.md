# Fix packages list page: image crop ratio, filter, and mobile Apply button

## Context
Follow-up to `fix-homepage-package-card-crop.md`. That fix addressed
the homepage; this one addresses the packages list page itself, using
the person's actual file content (pasted directly) rather than an
out-of-sync reference copy - a mismatch that caused an earlier
`jinja2.exceptions.TemplateRuntimeError: No filter named
'cloudinary_package_card' found` when instructions were given against
the wrong assumed baseline. Corrected by verifying every fix directly
against the person's pasted file content going forward.

## Fixes

**1. `app.py`** - added the `cloudinary_package_card` Jinja filter
(16:9 crop via `ar_16:9,c_fill,g_center`), separate from the existing
`cloudinary_card` filter (4:3, used by continent tiles, blog cards,
and the package detail gallery - unaffected by this change).

**2. `templates/packages/list_ajax.html`** - `pkg.image | cloudinary_card`
-> `pkg.image | cloudinary_package_card`, so package list cards use
the new 16:9 crop instead of 4:3.

**3. `templates/packages/list.html`, `.pkg-img-wrap`** -
`aspect-ratio: 4 / 3` -> `16 / 9`, so the CSS container matches the
now-16:9 served image instead of re-cropping it a second time.

**4. Same file, loading skeleton** - the shimmer placeholder's
`aspect-ratio:4/3` inline style updated to `16/9` to match, so the
loading state doesn't flash the old ratio before snapping to the new
one.

**5. Same file, unrelated bug found while reading the actual file** -
the mobile "collapsed by default" rule had a stray `s` typo:
`.filter-label,s` instead of `.filter-label,`. This turned
`#btn-apply` into part of an invalid compound selector that never
matched, so the Apply button was never actually hidden on mobile
before tapping "Filters." Removed the stray character.

## Verification
- Brace balance on `list.html`: 302/302 matched.
- Confirmed zero remaining instances of the old `4:3` ratio or the
  `,s` typo, and confirmed both `16 / 9` occurrences landed correctly.
- Full test suite: 512/512 passing.
- Rendered `/packages/` through an actual Flask test client: 200 OK,
  confirmed `aspect-ratio: 16 / 9` is served, confirmed the typo is
  gone, confirmed the `.filter-label,` selector is intact.
- Crop simulation against the person's real `melbourne_head.jpg`
  (1414x782, already documented in the homepage fix) applies
  identically here now that both the filter and the CSS agree on
  16:9 - only ~6px lost per side, logo and title fully intact.

No migration needed - one Python filter added, three small template
edits.
