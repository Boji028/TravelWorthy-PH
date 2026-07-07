# Cleanup: Orphaned static/images files

**Date:** 2026-07-02

## What changed

Added `scripts/clean_static_images.py`, a safe preview/delete utility that
cross-references every file in `static/images/` against:

- A safelist of 53 files hardcoded into templates/CSS (About page assets,
  logo, `beach.jpg`, `default_tour.jpg`, etc.)
- Every DB field that can reference a file in `static/images/`:
  `TourPackage.image`, `TourPackage.flier_image`, `PackageImage.path`,
  `Testimonial.image`, `TestimonialImage.path`, `BlogPost.featured_image`,
  `VisaCountry.requirements_pdf`, `Country.image`,
  `SiteSettings.hero_image` / `testimonial_image` / `cta_image`

Ran against production PostgreSQL and confirmed 34 orphaned files
(~22.5 MB) with zero references anywhere in the DB or codebase:

- 17 old prototype-era destination photos (BORACAY-*, KOREA_*,
  TAIPEITAICHUNG.jpg, HAWAIIAN.jpg, HONGKONG_MACAU_CANTON.jpg,
  Chengdu_chongqing.jpg, AFFORDABLE_TAIWAN.png, BARCELONA.jpg,
  star_voayger.jpg, istockphoto-1427530267-170667a.jpg, brand_logo.png,
  melbourne.jpg, south_korea.jpg)
- 1 stale visa PDF (`Japan_Tourist_Visa_Requirements_as_of_April_2026.pdf`)
- 16 hash-named upload leftovers (`package_*.jpg`, `review_*.jpg`,
  `blog_*.png`) with no matching DB records — likely pre-dating the
  switch to Cloudinary-hosted images for these records
- `README.txt`

All 34 files deleted via `python scripts/clean_static_images.py --delete`.

## Why

`static/images/` had accumulated 87 files over the project's lifetime;
only 53 are actually referenced (template-hardcoded About page assets).
The rest were dead weight from earlier prototyping and pre-Cloudinary
uploads, bloating the repo and the deployed static folder for no reason.

## Notes for future cleanups

`scripts/clean_static_images.py` can be re-run any time as a safe preview
(`python scripts/clean_static_images.py`, no `--delete`) to catch new
orphans before they accumulate again.
