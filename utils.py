"""Image and file utility functions."""
from typing import Optional, Any, Dict
import os
from PIL import Image
from flask import current_app


UPLOAD_FOLDER_KEY = 'UPLOAD_FOLDER'


def delete_old_image(filename: str, upload_folder: str) -> None:
    """Delete an old uploaded image file if it exists and is not the default.
    
    Args:
        filename: The image filename to delete
        upload_folder: Path to the upload directory
    """
    if not filename or filename == 'default_tour.jpg':
        return
    # Strip leading path components — stored values may be '/static/images/foo.jpg'
    basename = os.path.basename(filename)
    full_path = os.path.join(upload_folder, basename)
    if os.path.isfile(full_path):
        try:
            os.remove(full_path)
        except OSError as e:
            current_app.logger.warning(f'Failed to delete image {basename}: {e}')


def compress_image(file_path: str, max_size: int = 1200, quality: int = 82) -> None:
    """Resize, compress, and strip EXIF data from an image in-place.
    
    Keeps aspect ratio and removes sensitive metadata (GPS, camera info, etc).
    
    Args:
        file_path: Full path to image file
        max_size: Maximum dimension in pixels (default 1200)
        quality: JPEG quality 1-100 (default 82)
    
    Raises:
        FileNotFoundError: If file does not exist
        Exception: If file operations fail critically
    """
    try:
        with Image.open(file_path) as img:
            # Convert palette / RGBA to RGB for JPEG compatibility
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize only if larger than max_size on either axis
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.LANCZOS)
            
            # Strip EXIF and metadata (privacy protection)
            # This removes GPS, camera model, timestamps, etc.
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)
            
            # Save without metadata (format-aware, with proper error handling)
            file_ext = os.path.splitext(file_path)[1].lower()
            try:
                if file_ext in ['.jpg', '.jpeg']:
                    image_without_exif.save(file_path, format='JPEG', optimize=True, quality=quality)
                elif file_ext == '.png':
                    image_without_exif.save(file_path, format='PNG', optimize=True)
                elif file_ext == '.webp':
                    image_without_exif.save(file_path, format='WEBP', quality=quality)
                elif file_ext == '.gif':
                    image_without_exif.save(file_path, format='GIF', optimize=True)
                else:
                    # Fallback: let PIL determine format from extension
                    image_without_exif.save(file_path, optimize=True)
            except Exception as save_error:
                current_app.logger.error(f'Image save failed for {file_path}: {save_error}', exc_info=True)
                raise
            
    except FileNotFoundError as e:
        current_app.logger.error(f'Image file not found: {file_path}')
        raise
    except Exception as e:
        # Log the error but don't raise — we want to keep the original file if compression fails
        current_app.logger.error(f'Image compression failed for {file_path}: {e}', exc_info=True)


def save_image_metadata(db_object: Any, upload_result: Dict[str, Any], field_prefix: str = '') -> None:
    """Save image upload metadata to a database object.
    
    Convenience helper to save image upload metadata to a database object.
    
    Args:
        db_object: The database model instance to update
        upload_result: Result dict from ImageUploadService.upload_and_compress()
                      e.g., {'path': '2026-06/blog_123.jpg', 'size_kb': 125.5, 'uploaded_at': datetime}
        field_prefix: Prefix for field names (e.g., 'featured_image' or 'country_image')
                     Will update {field_prefix}_size_kb and {field_prefix}_uploaded_at
    
    Example:
        # Simple case (default prefix)
        result = ImageUploadService.upload_and_compress(file, 'blog')
        blog = BlogPost(...)
        blog.featured_image = result['path']
        save_image_metadata(blog, result, field_prefix='featured_image')
        
        # With custom prefix
        result = ImageUploadService.upload_and_compress(file, 'visa')
        visa = VisaCountry(...)
        visa.country_image = result['path']
        save_image_metadata(visa, result, field_prefix='country_image')
    """
    if not upload_result or not field_prefix:
        return
    
    # Set size field
    size_field = f'{field_prefix}_size_kb'
    if hasattr(db_object, size_field):
        setattr(db_object, size_field, upload_result.get('size_kb'))
    
    # Set upload timestamp field
    timestamp_field = f'{field_prefix}_uploaded_at'
    if hasattr(db_object, timestamp_field):
        setattr(db_object, timestamp_field, upload_result.get('uploaded_at'))

