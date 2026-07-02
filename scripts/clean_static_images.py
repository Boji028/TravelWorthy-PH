#!/usr/bin/env python3
"""
Clean up orphaned images in static/images/.

Checks static/images/ against:
  1. A safelist of files that are hardcoded into templates/CSS
     (About page assets, logo, default backgrounds, etc.) — these
     are never touched even if nothing else matches.
  2. Every DB record that can reference a file in static/images/:
     TourPackage.image, PackageImage.path, Testimonial.image,
     TestimonialImage.path, BlogPost.featured_image,
     VisaCountry.requirements_pdf,
     Country.image, SiteSettings.hero_image/testimonial_image/cta_image.

Anything left over is either genuinely orphaned or a Cloudinary-hosted
record (those store full https:// URLs, not local filenames, so they
never match a local file and are irrelevant here).

Usage:
    Preview only (safe - nothing gets deleted):
        python scripts/clean_static_images.py

    Actually delete orphaned files:
        python scripts/clean_static_images.py --delete
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models.blog import BlogPost
from models.package import TourPackage
from models.package_image import PackageImage
from models.testimonial import Testimonial
from models.testimonial_image import TestimonialImage
from models.visa import VisaCountry
from models.country import Country
from models.site_settings import SiteSettings

# Files that are hardcoded into templates/CSS rather than stored in the DB.
# Confirmed via full-codebase grep on 2026-07-02 — do not flag these even
# if the DB scan below doesn't find them.
SAFELIST = {
    'LOGO.jpg', 'PrimaryBG.jpg', 'beach.jpg', 'default_tour.jpg',
    'japan.jpg',
    'about-accred-baptta.png', 'about-accred-batangas-tourism.png',
    'about-accred-dot.png', 'about-accred-itatoa.png',
    'about-accred-love-ph.png', 'about-accred-philtoa.png',
    'about-accred-tap.png', 'about-accred-tpb.png',
    'about-partner-bdo.png', 'about-partner-cirrusglobal.png',
    'about-partner-dcx.png', 'about-partner-demeterland.png',
    'about-partner-dv-philippines.png', 'about-partner-efren-ramirez.png',
    'about-partner-joel-chavez.png', 'about-partner-sunlife.png',
    'about-dest-intl-australia.jpg', 'about-dest-intl-china.jpg',
    'about-dest-intl-europe.jpg', 'about-dest-intl-hong-kong.jpg',
    'about-dest-intl-indonesia.jpg', 'about-dest-intl-japan.jpg',
    'about-dest-intl-kazakhstan.jpg', 'about-dest-intl-malaysia.jpg',
    'about-dest-intl-maldives.jpg', 'about-dest-intl-singapore.jpg',
    'about-dest-intl-south-korea.jpg', 'about-dest-intl-taiwan.jpg',
    'about-dest-intl-thailand.jpg', 'about-dest-intl-uae.jpg',
    'about-dest-intl-usa.jpg', 'about-dest-intl-vietnam.jpg',
    'about-dest-local-bacolod.jpg', 'about-dest-local-baguio.jpg',
    'about-dest-local-batanes.jpg', 'about-dest-local-batangas.jpg',
    'about-dest-local-bicol.jpg', 'about-dest-local-bohol.jpg',
    'about-dest-local-boracay.jpg', 'about-dest-local-cebu.jpg',
    'about-dest-local-coron.jpg', 'about-dest-local-dumaguete.jpg',
    'about-dest-local-el-nido.jpg', 'about-dest-local-iloilo.jpg',
    'about-dest-local-puerto-galera.jpg',
    'about-dest-local-puerto-princesa.jpg',
    'about-dest-local-siargao.jpg', 'about-dest-local-siquijor.jpg',
}


def get_referenced_files():
    """Get all static/images filenames currently referenced in the DB."""
    referenced = set()

    for post in BlogPost.query.all():
        if post.featured_image:
            referenced.add(os.path.basename(post.featured_image))
            referenced.add(post.featured_image)

    for package in TourPackage.query.all():
        if package.image and package.image != 'default_tour.jpg':
            referenced.add(os.path.basename(package.image))
            referenced.add(package.image)
        if package.flier_image:
            referenced.add(os.path.basename(package.flier_image))
            referenced.add(package.flier_image)

    for pkg_image in PackageImage.query.all():
        if pkg_image.path:
            referenced.add(os.path.basename(pkg_image.path))
            referenced.add(pkg_image.path)

    for testimonial in Testimonial.query.all():
        if testimonial.image:
            referenced.add(os.path.basename(testimonial.image))
            referenced.add(testimonial.image)

    for t_image in TestimonialImage.query.all():
        if t_image.path:
            referenced.add(os.path.basename(t_image.path))
            referenced.add(t_image.path)

    # NOTE: VisaCountry.country_image was removed by migration
    # d7e1f5b3a9c4_remove_country_image_from_visa.py — only
    # requirements_pdf remains on this model.
    for visa in VisaCountry.query.all():
        if visa.requirements_pdf:
            referenced.add(os.path.basename(visa.requirements_pdf))
            referenced.add(visa.requirements_pdf)

    for country in Country.query.all():
        if country.image:
            referenced.add(os.path.basename(country.image))
            referenced.add(country.image)

    settings = SiteSettings.query.first()
    if settings:
        for field in ('hero_image', 'testimonial_image', 'cta_image'):
            value = getattr(settings, field, None)
            if value:
                referenced.add(os.path.basename(value))
                referenced.add(value)

    return referenced


def scan_static_images(images_folder, referenced, delete=False):
    """Scan static/images/ and find/delete orphaned files."""
    print(f"\n📂 Scanning: {images_folder}")
    print(f"🗄️  Database references {len(referenced)} distinct file values")
    print(f"🔒 Safelist protects {len(SAFELIST)} template-hardcoded files\n")

    orphaned = []
    total_size = 0

    for filename in sorted(os.listdir(images_folder)):
        full_path = os.path.join(images_folder, filename)
        if not os.path.isfile(full_path):
            continue
        if filename in SAFELIST:
            continue
        if filename in referenced:
            continue

        size = os.path.getsize(full_path)
        orphaned.append((filename, size))
        total_size += size

    if not orphaned:
        print("✅ No orphaned files found. static/images/ is clean.")
        return

    print(f"🗑️  Found {len(orphaned)} orphaned file(s), "
          f"{total_size / 1024:.1f} KB total:\n")
    for filename, size in orphaned:
        print(f"   - {filename}  ({size / 1024:.1f} KB)")

    if delete:
        print("\n🔥 Deleting...")
        for filename, _ in orphaned:
            os.remove(os.path.join(images_folder, filename))
            print(f"   ✔ removed {filename}")
        print(f"\n✅ Deleted {len(orphaned)} file(s), "
              f"freed {total_size / 1024:.1f} KB.")
    else:
        print("\nℹ️  Preview only — nothing was deleted. "
              "Re-run with --delete to actually remove these files.")


def main():
    delete = '--delete' in sys.argv

    app = create_app()
    with app.app_context():
        referenced = get_referenced_files()
        images_folder = os.path.join(app.root_path, 'static', 'images')
        scan_static_images(images_folder, referenced, delete=delete)


if __name__ == '__main__':
    main()
