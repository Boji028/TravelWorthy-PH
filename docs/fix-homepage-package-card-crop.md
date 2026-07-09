# Fix homepage featured packages using the wrong Cloudinary crop filter

## Context
Investigating why a package card image was clipping the "Travel Worthy"
logo led to two corrected assumptions and one real, confirmed gap:

1. `.pkg-img-wrap` (the packages list page card) was already
   `aspect-ratio: 16/9`, not `4:3` as stated earlier in conversation -
   that was inaccurate and is corrected here.
2. A dedicated `cloudinary_package_card` filter already exists in
   `app.py`, deliberately separate from the generic `cloudinary_card`
   filter, specifically to serve package images at 16:9 without
   affecting continent tiles, blog images, or other callers of the
   generic filter. Its docstring already documents exactly this
   problem (16:9 flier crops losing their logo/title under 4:3
   center-cropping).
3. **The real gap**: `templates/packages/list_ajax.html` (the
   packages list page) already correctly uses
   `pkg.image | cloudinary_package_card`. `templates/main/home.html`'s
   "Featured journeys" section, showing the exact same package images
   (`img_path`, built from `pkg.image` + `pkg.images[].path`), was
   still calling the generic `cloudinary_card` filter (4:3) - meaning
   the same image would display correctly on the packages list page
   but still get its logo clipped on the homepage.

`.tw-card-img` (the homepage card's CSS container) also used a fixed
`height: 200px` rather than a matching aspect ratio, which would
recreate the same double-crop problem diagnosed on the packages page
(server-side crop to one ratio, then a mismatched browser-side box
cropping it again) even after the filter was fixed.

## Fix
`templates/main/home.html`:
- Line ~376: `img_path | cloudinary_card` -> `img_path | cloudinary_package_card`
- `.tw-card-img`: `height: 200px` -> `aspect-ratio: 16 / 9`, matching
  the packages list page's `.pkg-img-wrap` and the corrected crop.

No changes needed to `app.py` or `list_ajax.html` - both were already
correct.

## Verification
- Confirmed every `cloudinary_card` vs `cloudinary_package_card` call
  site across the codebase: continent tiles, package detail gallery,
  and blog cards correctly stay on the generic 4:3 filter; packages
  list card and homepage featured packages now both use the dedicated
  16:9 filter consistently.
- Brace balance on `home.html`: 372/372 matched.
- Full test suite: 512/512 passing.
- Simulated the actual `ar_16:9,c_fill,g_center` transform against the
  person's real `melbourne_head.jpg` (1414x782, ratio 1.808): crops
  only 12px total off the width (6px each side) since the source is
  already very close to 16:9 - the logo and title are fully intact.

No migration needed - two small template edits.
