# Enhancement & Fix Changelog

## v2 — Security & Production Hardening (All 16 Issues Resolved)

### 🔴 Critical Fixes

**Fix 1 — Credentials & .gitignore**
- `.env` rotated with a new `SECRET_KEY` (generated via `secrets.token_hex(32)`)
- `ADMIN_PASSWORD` placeholder updated — change it before deploying
- `.gitignore` now comprehensively excludes `.env`, `*.db`, `instance/`, `uploads/`, `__pycache__/`
- `.env.example` created as a safe template to commit to source control

**Fix 2 — CSRF audit**
- All 25 POST-method templates audited — all confirmed to have `csrf_token` inputs
- Flask-WTF's `CSRFProtect` is initialized globally in `app.py`

**Fix 3 — Strong password policy**
- `is_strong_password()` helper added to `routes/auth.py`
- Minimum 12 characters, at least 1 uppercase letter, at least 1 digit
- Applied to both registration and the change-password flow on the profile page

---

### 🟠 Important Fixes

**Fix 4 — Atomic slot restoration on cancellation**
- `cancel_booking` now uses `db.session.execute(update(...).values(...))` — same
  atomic pattern as `book_package` — eliminating the race condition on concurrent cancellations

**Fix 5 — Numeric field validation in admin forms**
- `add_package` and `edit_package` wrap all `int()`/`float()` casts in `try/except`
- Returns a flash error and re-renders the form instead of raising a 500

**Fix 6 — Deprecated `get_or_404`**
- `main.py → delete_testimonial` updated from `Testimonial.query.get_or_404()`
  to `db.get_or_404(Testimonial, id)` — consistent with all other routes

**Fix 7 — Uploads separated from static assets**
- `UPLOAD_FOLDER` now points to `<app_root>/uploads/` instead of `static/images/`
- A `/uploads/<filename>` route serves user-uploaded files safely
- Eliminates risk of user files colliding with committed static assets
- For production, replace with S3/Cloudflare R2 + `boto3`

---

### 🟡 Moderate Fixes

**Fix 8 — Inline imports moved to top of files**
- `routes/packages.py`: `Continent`, `Country`, `VisaCountry` imports moved to module level
- `routes/main.py`: `TourPackage`, `ContactMessage` imports moved to module level

**Fix 9 — Flask-Migrate added**
- `Flask-Migrate>=4.0.0` added to `requirements.txt`
- `Migrate` initialized in `app.py` alongside other extensions
- Run once after pulling this update:
  ```bash
  flask db init
  flask db migrate -m "initial migration"
  flask db upgrade
  ```

**Fix 10 — N+1 query prevention**
- `models/booking.py`: relationship uses `lazy='select'` (explicit)
- `routes/admin.py → bookings()`: uses `joinedload(Booking.package)` to fetch
  package data in a single JOIN query instead of one query per row

**Fix 11 — Profile page booking limit**
- `routes/auth.py → profile()`: loads only the most recent 5 bookings instead
  of the full relationship (use the `/bookings/my-bookings` page for full history)

**Fix 12 — Email failures now logged**
- All call sites (`bookings.py`, `main.py`) catch email exceptions and emit
  `current_app.logger.warning(...)` instead of bare `except Exception: pass`
- Failures are visible in logs without blocking the user-facing response

---

### 🟢 Minor Fixes

**Fix 13 — Password minimum raised (covered by Fix 3)**
- Minimum raised from 6 to 12 characters with complexity requirements

**Fix 14 — Autocomplete rate limited**
- `/packages/autocomplete` now has `@limiter.limit("60 per minute")`

**Fix 15 — One-off scripts relocated**
- `create_visa_table.py`, `migrate_contact_user.py`, `migrate_inquiry_pax.py`,
  `update_inquiry.py` moved to `scripts/` with a README explaining their purpose

**Fix 16 — bleach `<a>` attributes restricted**
- `ALLOWED_BLOG_ATTRS = {'a': ['href', 'title']}` passed to all `bleach.clean()` calls
- Blocks `javascript:` URI schemes on anchor tags; only `href` and `title` are permitted

---

## v1 — Original Enhancements

### Security
- Rate limiting on `/auth/login` (5/min) and `/auth/register` (10/min)
- Blog/testimonial content sanitized with `bleach`
- Old image files deleted on replacement

### Performance
- Database indexes on `status`, `user_id`, `package_id`, `created_at`
- Image compression on every upload (Pillow, max 1200px, quality 82)
- `my_bookings` paginated (10 per page)

### User Experience
- Change password form on profile page

### Email Notifications
- `send_booking_confirmation`, `send_admin_new_booking`, `send_admin_new_inquiry`,
  `send_contact_autoreply`, `send_contact_admin_alert` — all in `email_service.py`

### Code Quality
- `decorators.py`, `utils.py`, `email_service.py` as shared helpers
- `save_image()` deduplicates upload logic in admin
- `FLASK_DEBUG` read from `.env`

### Production Readiness
- `gunicorn` + `Procfile` for Render/Railway/Heroku
- Switch `DATABASE_URL` to PostgreSQL for production
