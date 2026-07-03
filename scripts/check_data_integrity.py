#!/usr/bin/env python3
"""Data integrity checker for Travel Worthy PH.

Runs read-only consistency checks against the real database and prints
a report. Never modifies anything — safe to run anytime, against dev or
production.

Checks are tailored to this app's actual schema and the assumptions the
website's code makes about the data (singleton SiteSettings, one visa
agent, package images resolving to local files or Cloudinary URLs, etc).

Usage:
    python scripts/check_data_integrity.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

PASS = "  [OK]  "
WARN = "  [!!]  "

issues_found = 0


def check(title, rows, detail_fmt=None):
    """Print a check result. rows is a list of problem rows (empty = clean)."""
    global issues_found
    if not rows:
        print(f"{PASS}{title}")
        return
    issues_found += len(rows)
    print(f"{WARN}{title} — {len(rows)} issue(s):")
    for row in rows[:10]:
        if detail_fmt:
            print(f"          {detail_fmt(row)}")
        else:
            print(f"          {row}")
    if len(rows) > 10:
        print(f"          ... and {len(rows) - 10} more")


def q(sql):
    """Run a raw read-only query, return list of rows."""
    return db.session.execute(text(sql)).fetchall()


def run_checks(app):
    print("=" * 70)
    print("TRAVEL WORTHY PH — DATA INTEGRITY CHECK (read-only)")
    print("=" * 70)

    # ------------------------------------------------------------------
    print("\n--- Orphaned foreign keys ---")
    # These FKs have no DB-level ON DELETE CASCADE, so orphans can exist
    # if parent rows were ever deleted outside the ORM cascade paths.

    check(
        "Inquiries referencing a deleted package",
        q("""SELECT i.id, i.reference_number, i.package_id FROM inquiries i
             WHERE i.package_id IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM tour_packages p WHERE p.id = i.package_id)"""),
        lambda r: f"Inquiry {r[1]} (id={r[0]}) -> missing package_id={r[2]}",
    )
    check(
        "Inquiries referencing a deleted user",
        q("""SELECT i.id, i.reference_number, i.user_id FROM inquiries i
             WHERE i.user_id IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = i.user_id)"""),
        lambda r: f"Inquiry {r[1]} (id={r[0]}) -> missing user_id={r[2]}",
    )
    check(
        "Packages referencing a deleted country",
        q("""SELECT p.id, p.title, p.country_id FROM tour_packages p
             WHERE p.country_id IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM countries c WHERE c.id = p.country_id)"""),
        lambda r: f"Package '{r[1]}' (id={r[0]}) -> missing country_id={r[2]}",
    )
    check(
        "Packages assigned to a deleted agent",
        q("""SELECT p.id, p.title, p.assigned_agent_id FROM tour_packages p
             WHERE p.assigned_agent_id IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM agents a WHERE a.id = p.assigned_agent_id)"""),
        lambda r: f"Package '{r[1]}' (id={r[0]}) -> missing agent_id={r[2]}",
    )
    check(
        "Countries referencing a deleted continent",
        q("""SELECT c.id, c.name, c.continent_id FROM countries c
             WHERE c.continent_id IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM continents ct WHERE ct.id = c.continent_id)"""),
        lambda r: f"Country '{r[1]}' (id={r[0]}) -> missing continent_id={r[2]}",
    )
    check(
        "Package images whose package no longer exists",
        q("""SELECT pi.id, pi.package_id FROM package_images pi
             WHERE NOT EXISTS (SELECT 1 FROM tour_packages p WHERE p.id = pi.package_id)"""),
        lambda r: f"PackageImage id={r[0]} -> missing package_id={r[1]}",
    )
    check(
        "Notifications whose inquiry no longer exists",
        q("""SELECT n.id, n.inquiry_id FROM inquiry_notifications n
             WHERE NOT EXISTS (SELECT 1 FROM inquiries i WHERE i.id = n.inquiry_id)"""),
        lambda r: f"Notification id={r[0]} -> missing inquiry_id={r[1]}",
    )
    check(
        "Notifications whose user no longer exists",
        q("""SELECT n.id, n.user_id FROM inquiry_notifications n
             WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = n.user_id)"""),
        lambda r: f"Notification id={r[0]} -> missing user_id={r[1]}",
    )
    check(
        "Reviews whose package or user no longer exists",
        q("""SELECT r.id, r.package_id, r.user_id FROM package_reviews r
             WHERE NOT EXISTS (SELECT 1 FROM tour_packages p WHERE p.id = r.package_id)
             OR NOT EXISTS (SELECT 1 FROM users u WHERE u.id = r.user_id)"""),
        lambda r: f"Review id={r[0]} (package_id={r[1]}, user_id={r[2]})",
    )
    check(
        "Testimonials whose user no longer exists",
        q("""SELECT t.id, t.user_id FROM testimonials t
             WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = t.user_id)"""),
        lambda r: f"Testimonial id={r[0]} -> missing user_id={r[1]}",
    )
    check(
        "Testimonial images whose testimonial no longer exists",
        q("""SELECT ti.id, ti.testimonial_id FROM testimonial_images ti
             WHERE NOT EXISTS (SELECT 1 FROM testimonials t WHERE t.id = ti.testimonial_id)"""),
        lambda r: f"TestimonialImage id={r[0]} -> missing testimonial_id={r[1]}",
    )
    check(
        "Email verification tokens whose user no longer exists",
        q("""SELECT e.id, e.user_id FROM email_verification_tokens e
             WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = e.user_id)"""),
        lambda r: f"Token id={r[0]} -> missing user_id={r[1]}",
    )

    # ------------------------------------------------------------------
    print("\n--- Uniqueness & singleton assumptions ---")

    check(
        "Duplicate user emails (case-insensitive)",
        q("""SELECT LOWER(email), COUNT(*) FROM users
             GROUP BY LOWER(email) HAVING COUNT(*) > 1"""),
        lambda r: f"email '{r[0]}' appears {r[1]} times",
    )
    check(
        "SiteSettings singleton violated (code assumes exactly 0 or 1 row)",
        q("""SELECT id FROM site_settings OFFSET 1"""),
        lambda r: f"Extra SiteSettings row id={r[0]}",
    )
    check(
        "More than one visa agent (admin code enforces exclusivity)",
        q("""SELECT id, name FROM agents WHERE is_visa_agent = TRUE OFFSET 1"""),
        lambda r: f"Extra visa agent: {r[1]} (id={r[0]})",
    )
    check(
        "Duplicate inquiry reference numbers",
        q("""SELECT reference_number, COUNT(*) FROM inquiries
             GROUP BY reference_number HAVING COUNT(*) > 1"""),
        lambda r: f"reference '{r[0]}' appears {r[1]} times",
    )
    check(
        "OAuth accounts with provider but no oauth_id (or vice versa)",
        q("""SELECT id, email FROM users
             WHERE (oauth_provider IS NOT NULL AND oauth_id IS NULL)
             OR (oauth_provider IS NULL AND oauth_id IS NOT NULL)"""),
        lambda r: f"User {r[1]} (id={r[0]}) has inconsistent oauth fields",
    )
    check(
        "Accounts with neither a password nor an OAuth identity (can never log in)",
        q("""SELECT id, email FROM users
             WHERE password IS NULL AND oauth_provider IS NULL"""),
        lambda r: f"User {r[1]} (id={r[0]}) has no login method",
    )

    # ------------------------------------------------------------------
    print("\n--- Value sanity ---")

    check(
        "Inquiries with travel_date_to before travel_date_from",
        q("""SELECT id, reference_number FROM inquiries
             WHERE travel_date_to < travel_date_from"""),
        lambda r: f"Inquiry {r[1]} (id={r[0]})",
    )
    check(
        "Inquiries with zero or negative adults",
        q("""SELECT id, reference_number, num_adults FROM inquiries WHERE num_adults < 1"""),
        lambda r: f"Inquiry {r[1]} (id={r[0]}): num_adults={r[2]}",
    )
    check(
        "Packages with zero/negative price or duration",
        q("""SELECT id, title, price, duration_days FROM tour_packages
             WHERE price <= 0 OR duration_days <= 0"""),
        lambda r: f"Package '{r[1]}' (id={r[0]}): price={r[2]}, days={r[3]}",
    )
    check(
        "Reviews with rating outside 1-5",
        q("""SELECT id, rating FROM package_reviews WHERE rating < 1 OR rating > 5"""),
        lambda r: f"Review id={r[0]}: rating={r[1]}",
    )
    check(
        "Testimonials with rating outside 1-5",
        q("""SELECT id, rating FROM testimonials WHERE rating < 1 OR rating > 5"""),
        lambda r: f"Testimonial id={r[0]}: rating={r[1]}",
    )
    check(
        "Inquiries with unexpected status values",
        q("""SELECT id, reference_number, status FROM inquiries
             WHERE status NOT IN ('new', 'contacted', 'in_progress', 'confirmed', 'closed', 'cancelled', 'responded')"""),
        lambda r: f"Inquiry {r[1]} (id={r[0]}): status='{r[2]}'",
    )
    check(
        "Packages with unexpected package_type",
        q("""SELECT id, title, package_type FROM tour_packages
             WHERE package_type NOT IN ('domestic', 'international')"""),
        lambda r: f"Package '{r[1]}' (id={r[0]}): type='{r[2]}'",
    )

    # ------------------------------------------------------------------
    print("\n--- Files the data points at ---")
    # Local (non-Cloudinary) image/pdf paths should exist on disk.
    # Files can live in static/images (older uploads) or uploads/
    # (newer upload flow), so check both before flagging.
    local_dirs = [
        os.path.join(app.root_path, "static", "images"),
        os.path.join(app.root_path, "uploads"),
    ]

    def missing_local_files(rows, col_desc):
        missing = []
        for row in rows:
            value = row[2]
            if not value or value.startswith("http"):  # Cloudinary URLs — skip
                continue
            basename = os.path.basename(value)
            if not any(os.path.isfile(os.path.join(d, basename)) for d in local_dirs):
                missing.append((row[0], row[1], value))
        return missing

    check(
        "Package main images pointing at missing local files",
        missing_local_files(
            q("SELECT id, title, image FROM tour_packages WHERE image IS NOT NULL"),
            "image",
        ),
        lambda r: f"Package '{r[1]}' (id={r[0]}): {r[2]}",
    )
    check(
        "Visa requirement PDFs pointing at missing local files",
        missing_local_files(
            q("SELECT id, country_name, requirements_pdf FROM visa_countries WHERE requirements_pdf IS NOT NULL"),
            "requirements_pdf",
        ),
        lambda r: f"Visa '{r[1]}' (id={r[0]}): {r[2]}",
    )
    check(
        "Blog featured images pointing at missing local files",
        missing_local_files(
            q("SELECT id, title, featured_image FROM blog_posts WHERE featured_image IS NOT NULL"),
            "featured_image",
        ),
        lambda r: f"Post '{r[1]}' (id={r[0]}): {r[2]}",
    )

    # ------------------------------------------------------------------
    print("\n--- Summary counts (for eyeballing against the admin dashboard) ---")
    for table in [
        "users", "tour_packages", "inquiries", "countries", "continents",
        "agents", "blog_posts", "visa_countries", "testimonials",
        "package_reviews", "contact_messages", "inquiry_notifications",
    ]:
        count = q(f"SELECT COUNT(*) FROM {table}")[0][0]
        print(f"          {table:25} {count}")

    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    if issues_found == 0:
        print("RESULT: ALL CHECKS PASSED — no integrity issues found.")
    else:
        print(f"RESULT: {issues_found} issue(s) found — review the [!!] items above.")
        print("This script is read-only; nothing was modified.")
    print("=" * 70)


def main():
    app = create_app()
    with app.app_context():
        run_checks(app)


if __name__ == "__main__":
    main()
