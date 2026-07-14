# Activity log

Reverse-chronological log of working sessions. One entry per session,
newest first. Details for each fix live in their own kebab-case doc.

## 2026-07-12 — Full bug-hunt, fix, and test pass

Baseline: 537 passed. Swept the whole app for two known bug classes plus
general issues. Fixes (each has its own doc):

- user-delete-auth-token-cascade.md — PasswordResetToken /
  EmailVerificationToken missing cascade; deleting a user with a reset
  token 500'd. Models fixed, regression tests added.
- blog-list-pagination-missing.md — blog paginated at 10/page but had no
  pagination UI; older posts unreachable.
- visa-hero-reduced-motion-opacity.md — inline opacity vs reduced-motion
  media rule (the known CSS specificity bug class).
- visa-edit-validation-order-pdf-loss.md — failed validation after PDF
  replacement deleted the live PDF file.
- package-delete-orphaned-files.md — package delete leaked flier and
  gallery files in storage.
- gallery-image-duplicate-order.md — multi-image gallery upload gave all
  new images the same order value.
- testimonial-review-selectinload-n-plus-one.md — selectinload added to
  three testimonial/review queries.

Checked and clean: script-order bug class (all external-function calls in
templates are wrapped or event-driven), migration heads (exactly one),
timezone handling (app code consistently uses datetime.now(timezone.utc)),
flake8/mypy/pylint (no runtime bugs; pylint func.count E1102s are false
positives). Note: bandit is listed in requirements but not installed in
the venv.
