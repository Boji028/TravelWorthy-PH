# Image Metadata Tracking Guide

Your database now tracks when images are uploaded and how large they are. This helps you monitor storage usage and identify orphaned uploads.

## Database Changes

**Migration:** `001_add_image_metadata.py`

New columns added to all image-storing tables:
- `*_size_kb` - Image file size in kilobytes
- `*_uploaded_at` - Timestamp when image was uploaded

### Example Fields
```python
# BlogPost
featured_image_size_kb: float
featured_image_uploaded_at: datetime

# TourPackage  
image_size_kb: float
image_uploaded_at: datetime

# Testimonial
image_size_kb: float
image_uploaded_at: datetime
```

---

## Running the Migration

### Option A: Using Flask-Migrate (RECOMMENDED)
```bash
flask db upgrade
```

### Option B: Manual Setup
If you don't have previous migrations, run directly:
```python
python migrations/versions/001_add_image_metadata.py
```

---

## Updating Your Routes

### Before:
```python
# routes/admin.py
image_file = request.files.get('image')
if image_file and image_file.filename:
    filename = ImageUploadService.upload_and_compress(image_file, 'package')

package = TourPackage(
    title=title,
    image=filename,  # ← Just filename, no metadata
    ...
)
db.session.add(package)
db.session.commit()
```

### After:
```python
from utils import save_image_metadata  # ← Add import

image_file = request.files.get('image')
filename = 'default_tour.jpg'
upload_result = None

if image_file and image_file.filename:
    upload_result = ImageUploadService.upload_and_compress(image_file, 'package')
    filename = upload_result['path']

package = TourPackage(
    title=title,
    image=filename,
    ...
)

# Save metadata if upload succeeded
if upload_result:
    save_image_metadata(package, upload_result, field_prefix='image')

db.session.add(package)
db.session.commit()
```

---

## Routes to Update

Find these lines in `routes/admin.py` and update them:

### 1. Add Package (line ~107)
```python
# Before
filename = ImageUploadService.upload_and_compress(image_file, 'package')

# After
upload_result = ImageUploadService.upload_and_compress(image_file, 'package')
filename = upload_result['path']
# Then after creating package:
save_image_metadata(package, upload_result, field_prefix='image')
```

### 2. Edit Package (line ~167)
```python
# Before
new_img = ImageUploadService.upload_and_compress(image_file, 'package')
package.image = new_img

# After
upload_result = ImageUploadService.upload_and_compress(image_file, 'package')
package.image = upload_result['path']
save_image_metadata(package, upload_result, field_prefix='image')
```

### 3. Add Blog Post (line ~301)
```python
# Before
featured_image = ImageUploadService.upload_and_compress(featured_file, 'blog')

# After
upload_result = ImageUploadService.upload_and_compress(featured_file, 'blog')
featured_image = upload_result['path']
# Then after creating blog post:
save_image_metadata(blog_post, upload_result, field_prefix='featured_image')
```

### 4. Edit Blog Post (line ~341)
Same pattern as Edit Package

### 5. Add Visa Country (line ~560)
```python
# Before
image_filename = ImageUploadService.upload_and_compress(image_file, 'visa')

# After
upload_result = ImageUploadService.upload_and_compress(image_file, 'visa')
image_filename = upload_result['path']
# Then after creating visa:
save_image_metadata(visa, upload_result, field_prefix='country_image')
```

### 6. Edit Visa Country (line ~613)
Same pattern as above

### 7. Add/Edit Country (if exists)
Use field_prefix='image'

### 8. Add/Edit Continent (if exists)
Use field_prefix='image'

### 9. Testimonials in main.py (line ~91)
Use field_prefix='image'

---

## Benefits

Once metadata is saved, you can:

✅ **Monitor storage usage:**
```python
total_size = db.session.query(func.sum(TourPackage.image_size_kb)).scalar()
print(f"Total package images: {total_size} KB")
```

✅ **Find largest images:**
```python
huge = TourPackage.query.order_by(TourPackage.image_size_kb.desc()).limit(10)
```

✅ **See when images were uploaded:**
```python
recent = BlogPost.query.filter(
    BlogPost.featured_image_uploaded_at > datetime.now() - timedelta(days=7)
).all()
```

✅ **Improve cleanup script:**
The cleanup script can now compare DB metadata with actual files on disk to verify images exist before deleting.

---

## Summary

1. Run migration: `flask db upgrade`
2. Import helper: `from utils import save_image_metadata`
3. Wrap each upload: `upload_result = ImageUploadService.upload_and_compress(...)`
4. Save metadata: `save_image_metadata(db_object, upload_result, field_prefix='...')`
5. Commit changes

That's it! Your uploads are now fully tracked.
