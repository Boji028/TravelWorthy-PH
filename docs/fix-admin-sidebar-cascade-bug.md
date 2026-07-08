# Fix cascade-order bug in the admin sidebar mobile drawer

## Problem
After applying the previous fix (`add-admin-mobile-sidebar-drawer.md`),
the sidebar was still showing as a static, always-visible panel
instead of collapsing into the off-canvas drawer, at every phone
width.

## Root cause
Same class of bug as the earlier `.type-pills` fix on the packages
list page: `.admin-sidebar` and `.admin-main` each have an original,
pre-existing base rule (no media query) that lives further down in
`base_admin.html`, unrelated to this fix and untouched by it. The new
mobile media query rules for those two selectors were inserted
directly after `.admin-layout`, near the top of the style block -
which put them **before** those original base rules in the file.

Both the mobile rule and the base rule target the bare class name
with identical specificity (one class each). CSS resolves equal-
specificity ties by source order - later wins - regardless of which
one is wrapped in a media query. Since the original base rules
(`.admin-sidebar { position: sticky; ... }` and
`.admin-main { padding: 2rem; ... }`) came later in the file, they
silently overrode the new mobile rules at every viewport width,
canceling the drawer's `position: fixed` / `transform` and the
content padding reduction.

Traced this with a small script that walks every `.admin-*` rule in
the file, tags each as inside-media or not, and flags any mobile rule
that loses to a later non-media rule of equal-or-higher specificity -
confirmed exactly these two were affected, nothing else.

## Fix
Raised the specificity of both mobile rules from a bare class to a
descendant selector qualified by their parent, so they win regardless
of where the original rule sits in the file:

- `.admin-sidebar` -> `.admin-layout .admin-sidebar` (inside the
  media query only)
- `.admin-main` -> `.admin-layout .admin-main` (inside the media
  query only)

This is the same fix strategy used for `.type-pills` earlier - don't
rely on reordering code, make the override structurally win.

Also confirmed `.admin-sidebar.admin-sidebar-open` (the "open" state
rule) still correctly wins over the newly-qualified closed-state rule
when both apply: both are two-class selectors (equal specificity),
and the open-state rule already sits later within the same media
query, so the existing source order there was already correct and
didn't need changing.

## Verification
- Wrote a script that computes specificity for every `.admin-*`
  selector in the file and checks every mobile rule against every
  later non-media rule targeting the same selector - zero conflicts
  found after the fix (previously flagged exactly the two described
  above).
- Brace balance: 120/120 matched.
- Full test suite: 512/512 passing.
- Rendered `/admin/` through an actual Flask test client and
  confirmed the served HTML contains the corrected
  `.admin-layout .admin-sidebar` and `.admin-layout .admin-main`
  selectors, that the old vulnerable bare-selector pattern is gone,
  and the toggle button is present.

No migration needed - two selector names changed in one template.
