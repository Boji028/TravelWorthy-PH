# Add database integrity checker script

**Date:** 2026-07-03

## What changed

Added `scripts/check_data_integrity.py` — a strictly read-only
consistency checker that runs 25+ checks against the real database
and prints a pass/fail report. Never modifies data; safe to run
against dev or production anytime.

Checks are tailored to this app's actual schema and code assumptions:

- **Orphaned foreign keys** (12 checks): every FK relationship in the
  models — inquiries→packages/users, packages→countries/agents,
  countries→continents, package_images→packages,
  notifications→inquiries/users, reviews→packages/users,
  testimonials→users, testimonial_images→testimonials,
  verification_tokens→users
- **Uniqueness/singleton assumptions**: case-insensitive duplicate
  emails, SiteSettings singleton, visa-agent exclusivity (the admin
  code enforces at most one), duplicate inquiry reference numbers,
  inconsistent oauth_provider/oauth_id pairs, and accounts with
  neither password nor OAuth identity (unable to log in at all)
- **Value sanity**: backwards travel dates, non-positive adults/
  price/duration, out-of-range ratings, unexpected status and
  package_type values
- **File references**: package images, visa PDFs, and blog images
  whose local (non-Cloudinary) paths don't resolve on disk — checks
  both static/images/ and uploads/
- **Table counts**: quick census across all 12 main tables for
  eyeballing against the admin dashboard

## First run result

**All checks pass — zero real integrity issues found** across the
entire database: no orphans, no duplicates, no broken references,
valid values throughout, and every file reference resolves.

Two initial false positives were script inaccuracies, both fixed:
- 'contacted' is a legitimate inquiry status used by the admin panel;
  added to the script's valid-status list
- Visa PDFs live in uploads/, not static/images/; the file check now
  looks in both locations

## Why

Complements the existing test layers: pytest verifies the *code*
handles data correctly against fresh fixtures, and the live QA pass
verifies the *running app* behaves; this script verifies the *actual
accumulated data* is consistent — catching drift from manual admin
edits, old migrations, or cleanup scripts that predate current
cascade rules. Intended to be run before deployments and after any
bulk data operation.
