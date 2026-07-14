# visa_edit: failed validation could delete the live requirements PDF

## What was wrong
In `admin.visa_edit` the PDF-replacement block ran before the price and
documents-count validation. The PDF block saves the new file, deletes the
old PDF from storage, and mutates `visa.requirements_pdf` on the model.
If a later validation check then failed (e.g. negative price), the route
redirected without committing — the session change was discarded, so the
DB kept pointing at the old filename, but that file had already been
deleted from disk. Result: the public visa page's "View requirements"
button served a dead PDF link until an admin re-uploaded it.

## Fix
Reordered `admin.visa_edit` so the numeric validation (price,
documents_count) runs first and the PDF replacement runs last, with a
comment explaining why the order matters: the PDF step is the only one
with an irreversible side effect (deleting the old file), so nothing that
can fail is allowed to run after it.

## Why the fix is correct
All early returns now happen before any file is touched. Once the PDF
block runs, the only remaining steps are plain model assignments and the
commit, which cannot fail validation. The same validate-then-mutate order
is already used by `edit_package` and `edit_blog`.
