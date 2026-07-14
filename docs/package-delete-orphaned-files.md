# Package delete left flier and gallery files orphaned in storage

## What was wrong
Deleting a package cleaned up its DB rows (gallery `PackageImage` rows
cascade correctly) but leaked the underlying files:

- `admin.delete_package` (single delete) removed only `package.image` from
  storage — never the flier, even though the bulk-delete path already
  removed both. Inconsistent and leaks one file per package with a flier.
- Neither the single nor the bulk path removed gallery image files. Every
  deleted package left all of its gallery photos behind in
  Cloudinary/uploads forever.

Not a crash, but a steady storage leak on a Cloudinary account with a
quota, and orphans are invisible once the DB rows are gone.

## Fix
`routes/admin.py`:
- `delete_package` now also deletes `package.flier_image` and iterates
  `package.images` deleting each gallery file before the row delete.
- `bulk_package_action` delete branch does the same gallery-file loop
  (it already handled image + flier).

`delete_old_image()` is None-safe and swallows per-file errors, so
packages without fliers/galleries and already-missing files are fine.
