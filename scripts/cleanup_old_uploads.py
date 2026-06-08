#!/usr/bin/env python3
"""
Cleanup script to remove old/orphaned uploaded images.
Run periodically via cron (Linux/Mac) or Task Scheduler (Windows).

Usage:
    python cleanup_old_uploads.py --days 90
    
This will delete images older than 90 days that are NOT referenced in the database.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models.blog import BlogPost
from models.package import TourPackage
from models.testimonial import Testimonial
from models.visa import VisaCountry
from models.country import Country
from models.continent import Continent


def get_referenced_images():
    """Collect all image filenames referenced in the database."""
    referenced = set()
    
    # BlogPost images
    for post in BlogPost.query.all():
        if post.featured_image:
            referenced.add(post.featured_image)
    
    # TourPackage images
    for package in TourPackage.query.all():
        if package.image and package.image != 'default_tour.jpg':
            referenced.add(package.image)
    
    # Testimonial images
    for testimonial in Testimonial.query.all():
        if testimonial.image:
            referenced.add(testimonial.image)
    
    # VisaCountry images
    for visa in VisaCountry.query.all():
        if visa.country_image:
            referenced.add(visa.country_image)
        if visa.requirements_pdf:
            referenced.add(visa.requirements_pdf)
    
    # Country images
    for country in Country.query.all():
        if country.image:
            referenced.add(country.image)
    
    # Continent images
    for continent in Continent.query.all():
        if continent.image:
            referenced.add(continent.image)
    
    return referenced


def cleanup_uploads(upload_folder, days_old=90, dry_run=False):
    """
    Delete orphaned images older than specified days.
    
    Args:
        upload_folder: Path to uploads directory
        days_old: Delete files older than this many days
        dry_run: If True, only print what would be deleted (don't actually delete)
    
    Returns:
        tuple: (deleted_count, freed_space_mb)
    """
    cutoff_date = datetime.now() - timedelta(days=days_old)
    referenced_images = get_referenced_images()
    
    deleted_count = 0
    freed_space_bytes = 0
    
    print(f"\n📂 Scanning uploads folder: {upload_folder}")
    print(f"🗑️  Looking for images older than {days_old} days (before {cutoff_date.strftime('%Y-%m-%d')})")
    print(f"📊 Database references {len(referenced_images)} images\n")
    
    for root, dirs, files in os.walk(upload_folder):
        for file in files:
            filepath = os.path.join(root, file)
            
            # Get file age
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            # Build relative path for database comparison (e.g., "2026-06/blog_abc123.jpg")
            relative_path = os.path.relpath(filepath, upload_folder)
            relative_path = relative_path.replace(os.sep, '/')  # Normalize to forward slashes
            
            # Check if file is old and not referenced
            if file_time < cutoff_date and relative_path not in referenced_images:
                file_size = os.path.getsize(filepath)
                freed_space_bytes += file_size
                
                if dry_run:
                    print(f"  [DRY RUN] Would delete: {relative_path} ({file_size / 1024:.1f} KB)")
                else:
                    try:
                        os.remove(filepath)
                        print(f"  ✓ Deleted: {relative_path} ({file_size / 1024:.1f} KB)")
                        deleted_count += 1
                    except Exception as e:
                        print(f"  ✗ Failed to delete {relative_path}: {e}")
    
    freed_space_mb = freed_space_bytes / (1024 * 1024)
    
    if dry_run:
        print(f"\n[DRY RUN] Would delete {deleted_count} files, freeing {freed_space_mb:.2f} MB")
    else:
        print(f"\n✅ Deleted {deleted_count} files, freed {freed_space_mb:.2f} MB")
    
    return deleted_count, freed_space_mb


def main():
    parser = argparse.ArgumentParser(description='Clean up old orphaned uploaded images')
    parser.add_argument('--days', type=int, default=90, help='Delete images older than N days (default: 90)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        upload_folder = app.config.get('UPLOAD_FOLDER')
        
        if not upload_folder or not os.path.exists(upload_folder):
            print(f"Error: Upload folder not found at {upload_folder}")
            sys.exit(1)
        
        cleanup_uploads(upload_folder, days_old=args.days, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
