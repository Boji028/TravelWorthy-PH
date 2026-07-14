# edit_package: all gallery images added in one request got the same order

## What was wrong
`admin.edit_package` set each new gallery image's `order` to
`len(package.images)`. Pending `db.session.add()` objects are not part of
the `package.images` collection until flush, so when an admin added
several photos in a single save, every one of them received the identical
order value. `TourPackage.images` is ordered by `PackageImage.order`, so
the display order of those photos was then decided by the tiebreaker
(insertion id) — effectively undefined and impossible to correct without
touching the DB.

## Fix
Capture `next_order = len(package.images)` once, then increment it for
each image actually added (both the direct-Cloudinary-URL loop and the
file-upload fallback loop share the counter). New images now get strictly
increasing, unique order values appended after the existing ones.
