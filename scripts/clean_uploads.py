#!/usr/bin/env python3
"""
Clean up orphaned images in the uploads folder.
These are files that exist on disk but have no matching database record.

Usage:
    Preview only (safe - nothing gets deleted):
        python scripts/clean_uploads.py

    Actually delete orphaned files:
        python scripts/clean_uploads.py --delete
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models.blog import BlogPost
from models.package import TourPackage
from models.testimonial import Testimonial
from models.visa import VisaCountry
from models.country import Country


def get_referenced_files():
    """Get all file paths currently referenced in the database."""
    referenced = set()

    for post in BlogPost.query.all():
        if post.featured_image:
            referenced.add(os.path.basename(post.featured_image))
            referenced.add(post.featured_image)

    for package in TourPackage.query.all():
        if package.image and package.image != 'default_tour.jpg':
            referenced.add(os.path.basename(package.image))
            referenced.add(package.image)

    for testimonial in Testimonial.query.all():
        if testimonial.image:
            referenced.add(os.path.basename(testimonial.image))
            referenced.add(testimonial.image)

    for visa in VisaCountry.query.all():
        if visa.country_image:
            referenced.add(os.path.basename(visa.country_image))
            referenced.add(visa.country_image)
        if visa.requirements_pdf:
            referenced.add(os.path.basename(visa.requirements_pdf))
            referenced.add(visa.requirements_pdf)

    for country in Country.query.all():
        if country.image:
            referenced.add(os.path.basename(country.image))
            referenced.add(country.image)

    return referenced


def scan_uploads(upload_folder, referenced, delete=False):
    """Scan uploads folder and find/delete orphaned files."""
    print(f"\n📂 Scanning: {upload_folder}")
    print(f"🗄️  Database references {len(referenced)} files\n")

    orphaned = []
    total_size = 0

    for root, dirs, files in os.walk(upload_folder):
        for filename in files:
            filepath = os.path.join(root, filename)
            relative = os.path.relpath(filepath, upload_folder).replace(os.sep, '/')
            size_kb = os.path.getsize(filepath) / 1024

            is_referenced = (
                filename in referenced or
                relative in referenced
            )

            if not is_referenced:
                orphaned.append((filepath, relative, size_kb))
                total_size += size_kb

    if not orphaned:
        print("✅ No orphaned files found! Everything is clean.")
        return

    print(f"Found {len(orphaned)} orphaned files ({total_size / 1024:.2f} MB total):\n")

    for filepath, relative, size_kb in orphaned:
        if delete:
            try:
                os.remove(filepath)
                print(f"  🗑️  Deleted: {relative} ({size_kb:.1f} KB)")
            except Exception as e:
                print(f"  ❌ Failed to delete {relative}: {e}")
        else:
            print(f"  📄 {relative} ({size_kb:.1f} KB)")

    print()
    if delete:
        print(f"✅ Deleted {len(orphaned)} files, freed {total_size / 1024:.2f} MB")
    else:
        print(f"⚠️  Preview only — nothing was deleted.")
        print(f"   To actually delete, run: python scripts/clean_uploads.py --delete")


def main():
    delete_mode = '--delete' in sys.argv

    print("=" * 60)
    print("🧹 Uploads Cleanup Tool")
    print("=" * 60)

    if delete_mode:
        print("⚠️  MODE: DELETE (files will be permanently removed!)")
    else:
        print("👁️  MODE: PREVIEW (nothing will be deleted)")

    app = create_app()
    with app.app_context():
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if not upload_folder or not os.path.exists(upload_folder):
            print(f"❌ Upload folder not found: {upload_folder}")
            sys.exit(1)

        referenced = get_referenced_files()
        scan_uploads(upload_folder, referenced, delete=delete_mode)


if __name__ == '__main__':
    main()
