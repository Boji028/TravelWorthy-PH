"""Image upload and processing service with validation and compression."""
from typing import Dict, Any, Optional, Set
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import current_app
from PIL import Image


class ImageUploadException(Exception):
    """Custom exception for image upload errors."""
    pass


class ImageUploadService:
    """Centralized service for handling image uploads with validation and compression."""
    
    ALLOWED_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    MAX_IMAGE_SIZE_MB: int = 25  # Maximum file size in MB
    MAX_IMAGE_DIMENSION: int = 10000  # Maximum pixel dimension to prevent zip bombs
    
    @staticmethod
    def is_allowed(filename: Optional[str]) -> bool:
        """Check if file extension is allowed.
        
        Args:
            filename: The filename to check
            
        Returns:
            True if extension is allowed, False otherwise
        """
        if not filename:
            return False
        ext = os.path.splitext(filename)[1].lower()
        return ext in ImageUploadService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file: Optional[FileStorage]) -> None:
        """Validate that file size is within limits.
        
        Args:
            file: FileStorage object from request.files
        
        Raises:
            ImageUploadException: If file is too large
        """
        if not file:
            return
        
        # Get file size
        file.seek(0, os.SEEK_END)
        file_size_bytes = file.tell()
        file.seek(0)
        
        max_size_bytes = ImageUploadService.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            raise ImageUploadException(
                f'File too large. Maximum size: {ImageUploadService.MAX_IMAGE_SIZE_MB}MB '
                f'(your file: {file_size_bytes / (1024 * 1024):.1f}MB)'
            )
    
    @staticmethod
    def validate_image_format(file: FileStorage) -> None:
        """Validate that file is actually a valid image and not disguised executable.
        
        Args:
            file: FileStorage object from request.files
        
        Raises:
            ImageUploadException: If file is not a valid image
        """
        try:
            file.seek(0)
            with Image.open(file) as img:
                # Check dimensions to prevent decompression bombs
                if max(img.size) > ImageUploadService.MAX_IMAGE_DIMENSION:
                    raise ImageUploadException(
                        f'Image dimensions too large. Max: {ImageUploadService.MAX_IMAGE_DIMENSION}px'
                    )
                # Validate it's an actual image format
                img.verify()
            file.seek(0)
        except ImageUploadException:
            raise
        except Exception as e:
            raise ImageUploadException(f'Invalid image file: {str(e)}')
    
    @staticmethod
    def upload_and_compress(file: Optional[FileStorage], prefix: str = 'img') -> Dict[str, Any]:
        """Validate, save, and compress an uploaded image into date-based folder.
        
        Args:
            file: FileStorage object from request.files
            prefix: Prefix for generated filename (e.g., 'blog', 'review', 'visa')
        
        Returns:
            dict: {
                'path': '2026-06/blog_abc123def456.jpg',
                'size_kb': 125.5,
                'uploaded_at': datetime object
            }
        
        Raises:
            ImageUploadException: If validation fails or file operations error
        """
        from flask import current_app
        
        if not file or not file.filename:
            raise ImageUploadException('No file selected')
        
        if not ImageUploadService.is_allowed(file.filename):
            raise ImageUploadException(
                f'Invalid file type. Allowed types: {", ".join(ImageUploadService.ALLOWED_EXTENSIONS)}'
            )
        
        # Validate file size before processing
        try:
            ImageUploadService.validate_file_size(file)
        except ImageUploadException as e:
            current_app.logger.warning(f"File size validation failed: {e}")
            raise
        
        # Validate it's actually an image
        try:
            ImageUploadService.validate_image_format(file)
        except ImageUploadException as e:
            current_app.logger.warning(f"Image format validation failed: {e}")
            raise
        
        temp_filepath = None
        try:
            ext = os.path.splitext(secure_filename(file.filename))[1].lower()
            filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
            
            # Create date-based subfolder (YYYY-MM)
            date_folder = datetime.now().strftime('%Y-%m')
            upload_timestamp = datetime.now()
            
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if not upload_folder:
                current_app.logger.error("Upload folder not configured")
                raise ImageUploadException('Upload folder not configured')
            
            # Ensure upload folder exists
            if not os.path.exists(upload_folder):
                try:
                    os.makedirs(upload_folder, exist_ok=True)
                except OSError as e:
                    current_app.logger.error(f"Failed to create upload folder: {e}", exc_info=True)
                    raise ImageUploadException('Failed to create upload directory')
            
            # Full path with date subfolder
            date_based_folder = os.path.join(upload_folder, date_folder)
            try:
                os.makedirs(date_based_folder, exist_ok=True)
            except OSError as e:
                current_app.logger.error(f"Failed to create date-based folder: {e}", exc_info=True)
                raise ImageUploadException('Failed to create upload subdirectory')
            
            filepath = os.path.join(date_based_folder, filename)
            
            # Check for file conflicts (extremely unlikely with UUID, but be safe)
            if os.path.exists(filepath):
                current_app.logger.warning(f"File already exists: {filepath}, regenerating filename")
                # Regenerate filename with UUID
                filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(date_based_folder, filename)
            
            # Save file
            try:
                file.seek(0)
                file.save(filepath)
                temp_filepath = filepath
                current_app.logger.debug(f"Image file saved: {filepath}")
            except IOError as e:
                current_app.logger.error(f"Failed to save image file {filepath}: {e}", exc_info=True)
                raise ImageUploadException(f'Failed to save image: {str(e)}')
            
            # Compress the image with error handling
            try:
                from utils import compress_image
                compress_image(filepath)
                current_app.logger.debug(f"Image compressed: {filepath}")
            except FileNotFoundError:
                current_app.logger.error(f"Image file disappeared after save: {filepath}")
                raise ImageUploadException('Image file was lost during processing')
            except Exception as e:
                current_app.logger.error(f"Image compression failed for {filepath}: {e}", exc_info=True)
                # Don't fail completely if compression fails - try to use uncompressed version
                if not os.path.exists(filepath):
                    raise ImageUploadException(f'Image processing error: {str(e)}')
                current_app.logger.warning(f"Using uncompressed image due to compression error: {filepath}")
            
            # Get file size after compression (in KB)
            try:
                file_size_bytes = os.path.getsize(filepath)
                file_size_kb = file_size_bytes / 1024
            except OSError as e:
                current_app.logger.error(f"Failed to get file size for {filepath}: {e}")
                file_size_kb = 0
            
            # Return metadata dict
            relative_path = f"{date_folder}/{filename}"
            result = {
                'path': relative_path,
                'size_kb': round(file_size_kb, 2),
                'uploaded_at': upload_timestamp
            }
            
            current_app.logger.info(f"Image uploaded successfully: {relative_path} ({file_size_kb:.1f}KB)")
            return result
            
        except ImageUploadException:
            # Clean up on known exceptions
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                    current_app.logger.debug(f"Cleaned up failed upload: {temp_filepath}")
                except OSError as e:
                    current_app.logger.warning(f"Failed to clean up temp file {temp_filepath}: {e}")
            raise
        except Exception as e:
            # Clean up on unexpected exceptions
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass
            current_app.logger.error(f'Unexpected error during image upload: {e}', exc_info=True)
            raise ImageUploadException(f'Failed to upload image: {str(e)}')
    
    @staticmethod
    def delete_image(filename):
        """
        Delete an image file from uploads folder (handles date-based paths).
        
        Args:
            filename: Relative path to file (e.g., '2026-06/blog_abc123.jpg')
        
        Returns:
            bool: True if deleted, False if not found
        """
        if not filename:
            return False
        
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if not upload_folder:
                return False
            
            # Handle both old format (just filename) and new format (date/filename)
            filepath = os.path.join(upload_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            current_app.logger.warning(f'Failed to delete image {filename}: {e}')
            return False
