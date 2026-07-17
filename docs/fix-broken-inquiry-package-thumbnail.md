# Fix: broken package thumbnail on the inquiry page

**Date:** 2026-07-17

## What was wrong

The small package preview thumbnail on `templates/bookings/inquire_package.html`
always built its `src` as `/uploads/{{ package.image }}`. That's correct
only for legacy local uploads (a bare filename). Since the Cloudinary
migration, `TourPackage.image` is a full `https://res.cloudinary.com/...`
URL for every package uploaded since - so the template was producing
`/uploads/https://res.cloudinary.com/...`, a nonsense path that 404s,
hence the broken-image icon.

Every other place that renders `package.image` (`packages/detail.html`,
`admin/edit_package.html`) already branches on
`package.image.startswith('http')` and uses the URL as-is when it's a
Cloudinary link. This one template never got that treatment.

## Fix

Matched the existing pattern: Cloudinary URLs go through the
`cloudinary_card` filter (same transform used for other small
card-style thumbnails); bare filenames still get the `/uploads/`
prefix for backward compatibility with anything uploaded before the
Cloudinary migration.

## Tests

Added `test_cloudinary_image_thumbnail_not_prefixed_with_uploads` to
`tests/test_bookings.py` - creates a package with a Cloudinary-style
`image` URL, requests the inquire page, and asserts the response never
contains `/uploads/https://` and does contain the raw Cloudinary path.

Full suite: 574 passed (573 previous + 1 new), 2 pre-existing warnings
unrelated to this change.
