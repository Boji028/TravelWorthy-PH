# Consolidate the site's 8 scattered breakpoint values onto a 2-tier scale

## Problem
Across the codebase, 8 different `max-width` values were in use for
responsive breakpoints - 560, 600, 640, 680, 768, 780, 860, 900px -
scattered across 15 files with no consistent logic to which value went
where. This meant different parts of the same page (or different pages
entirely) could switch to their "mobile" layout at different viewport
widths, so an in-between width like an iPad's 820px got inconsistent
treatment depending on which component you looked at.

## Fix
Standardized every breakpoint onto one of two values, based on what
job each one was actually doing:

- **`max-width: 768px`** ("phone" tier) - for rules that stack a row
  into a column, reduce padding, or shrink type. These only need to
  kick in for phone-width screens.
- **`max-width: 1024px`** ("tablet" tier) - for rules that collapse a
  multi-column grid or a two-panel split layout down to fewer columns.
  These need to kick in earlier (tablets need it too, not just
  phones), matching the nav breakpoint fixed earlier this session.

| File | Old value(s) | New value | Reason |
|---|---|---|---|
| `templates/main/home.html` | 640 (wave scaling) | 768 | phone-tier decorative scaling |
| `templates/main/home.html` | 900 (tiles/why-grid/stories columns) | 1024 | tablet-tier grid collapse |
| `templates/main/home.html` | 560 (search bar stacking) | 768 | phone-tier stacking |
| `templates/main/my_inquiries.html` | 560 (row stacking) | 768 | phone-tier stacking |
| `templates/admin/testimonials.html` | 600 (header/actions stacking) | 768 | phone-tier stacking |
| `templates/main/inquiry_status.html` | 600 (details grid) | 768 | phone-tier stacking |
| `templates/bookings/inquire_package.html` | 600 (form-row/hero/preview) | 768 | phone-tier stacking |
| `templates/bookings/plan_my_trip.html` | 860 (pmt-split columns) | 1024 | tablet-tier split collapse |
| `templates/bookings/plan_my_trip.html` | 600 (form-row/heading) | 768 | phone-tier stacking |
| `templates/auth/register.html` | 640 (card padding/form-row) | 768 | phone-tier stacking |
| `templates/auth/profile.html` | 680 (header/grid stacking) | 768 | phone-tier stacking |
| `templates/main/about.html` | 780 (why-grid columns) | 1024 | tablet-tier grid collapse |
| `templates/main/about.html` | 780 (service-list columns) | 1024 | tablet-tier grid collapse |
| `templates/main/about.html` | 780 (logo-grid columns) | 1024 | tablet-tier grid collapse |
| `templates/main/about.html` | 900 (dest-grid columns) | 1024 | tablet-tier grid collapse |

`static/css/main.css`'s nav breakpoint was already moved to 1024 in
the previous fix this session; not touched again here.

## Not changed (already correct)
Five files already used `768px` for genuinely phone-tier jobs
(stacking, padding, table horizontal-scroll) and were left as-is:
`admin/inquiries.html`, `packages/list.html`, `blog/list.html`, plus
the two flagged below.

## Flagged, not changed
`packages/detail.html` and `blog/detail.html` both collapse a
two-column (main content + sidebar) layout to single-column at their
existing `768px` breakpoint - structurally the same job as
`plan_my_trip.html`'s `.pmt-split` and `about.html`'s grids, which
were moved to `1024px` in this pass. These two were left alone since
they were already at a "canonical" value (768) and touching them
wasn't part of what was agreed - but they're worth a look, since a
sidebar+content layout is a common place for tablet-width cramping.

## Verification
- Sitewide breakpoint sweep: down from 8 distinct values to exactly 2
  (`768px` used 16 times, `1024px` used 7 times, plus the unrelated
  `prefers-reduced-motion` queries).
- Brace-balance check on all 9 edited templates: all matched.
- Full test suite: 512/512 passing (pure CSS changes, no Python
  touched).

No migration needed - template/stylesheet changes only.
