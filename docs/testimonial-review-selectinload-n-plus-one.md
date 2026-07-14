# N+1 fixes: testimonial and package-review user/image loads

## What was wrong
Three routes rendered lists whose templates access lazy relationships per
row, issuing one extra SELECT per item:

- `main.reviews` — 12 testimonials/page, template reads `t.user.name` and
  `t.images` per card: up to 25 queries per page view.
- `main.home` — 5 testimonials embedded into the carousel read
  `t.user.name` each: 5 extra queries on the busiest page of the site.
- `packages.package_detail` — every review reads `review.user.name`:
  unbounded (one query per review on the package).

## Fix
Added `selectinload()` options to the three queries (`Testimonial.user`,
`Testimonial.images`, `PackageReview.user`), matching the pattern the
codebase already uses for `TourPackage.images` on the home and list pages.
Each page now does a constant number of queries regardless of row count.

Flagged but not changed: `admin.testimonials` issues six COUNT queries for
the rating-filter pills (one per rating + total). Could be a single
GROUP BY, but it is an admin-only page at 20 rows/page — left as is to
keep the change minimal.
