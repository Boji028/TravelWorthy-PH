# About page - accreditations, partners, destinations

Date: 2026-07-01

## Summary
Added four new sections to `templates/main/about.html`: Why Choose Us (4 feature
cards), Our Services (12-item list), Accreditations & Partners (logo grid for 8
DOT/PHILTOA/etc accreditations and 8 client companies), and Destinations (photo
grid for 16 local + 16 international destinations). Source content and images
pulled from the company's 2019 corporate profile PDF.

Existing Our Story, Mission, Vision, and Tagline content left unchanged. CTA
moved from mid-page to the bottom of the page, after the new sections.

## Changes
- `templates/main/about.html`: added `.why-section` (why choose us),
  `.services-section` (our services), `.trust-section` (accreditations/partners),
  and `.dest-section` (destinations) markup and scoped CSS.
- `static/images/`: added 48 new flat files, prefixed `about-` to avoid
  collisions with existing assets (`about-accred-*.png`, `about-partner-*.png`,
  `about-dest-local-*.jpg`, `about-dest-intl-*.jpg`).

## Design notes
- Why Choose Us and Our Services use the standard site `--amber` (#EF8233) -
  only the accreditations/destinations sections below them are scoped to the
  PDF gold tone.
- New sections use a page-scoped CSS variable override (`.ab-pdf-scope { --amber:
  #FAAB1C; }`) so the accreditations/destinations sections match the PDF's gold
  tone while the rest of the site keeps the standard `--amber` (#EF8233).
- Reused existing `.ab-reveal` scroll animation and `Pogonia` heading font
  conventions already established in this template - no new patterns introduced.

## Known follow-ups
- Destination photos are stock photography sourced from the corporate PDF -
  confirm usage rights before treating this as final, or replace with owned
  photography.
- 32-tile destination grid is dense on mobile; consider capping to a curated
  set with a "see all" link if it feels heavy in testing.
- Images were optimized for web (trimmed PNGs, 640x480 JPEGs) but not run
  through the project's normal image pipeline, if one exists.

## Testing
- Not yet run against `pytest` - no existing about-page tests were touched,
  but confirm nothing asserts on old about.html structure before merging.
