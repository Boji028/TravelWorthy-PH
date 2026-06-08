"""Image upload service using Cloudinary for cloud storage."""
import os
from typing import Optional
import cloudinary
import cloudinary.uploader
from flask import current_app


class ImageUploadException(Exception):
    """Raised when an image upload fails."""
    pass


# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)


class ImageUploadService:
    """Handles image uploads to Cloudinary."""

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_IMAGE_SIZE_MB = 25
    MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

    @staticmethod
    def _allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in ImageUploadService.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def upload_and_compress(file, prefix: str = 'img') -> dict:
        """Upload an image to Cloudinary.

        Args:
            file: FileStorage object from Flask
            prefix: Folder/prefix for organizing uploads (e.g. 'package', 'review')

        Returns:
            dict with 'path' (full URL), 'size_kb', 'uploaded_at'

        Raises:
            ImageUploadException: if validation or upload fails
        """
        if not file or not file.filename:
            raise ImageUploadException('No file provided.')

        if not ImageUploadService._allowed_file(file.filename):
            raise ImageUploadException(
                f'Invalid file type. Allowed: {", ".join(ImageUploadService.ALLOWED_EXTENSIONS)}'
            )

        # Check file size
        file.seek(0, 2)  # Seek to end
        size_bytes = file.tell()
        file.seek(0)  # Reset

        if size_bytes > ImageUploadService.MAX_IMAGE_SIZE_BYTES:
            raise ImageUploadException(
                f'File too large. Maximum size is {ImageUploadService.MAX_IMAGE_SIZE_MB}MB.'
            )

        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file,
                folder=f'travelworthyph/{prefix}',
                transformation=[
                    {'quality': 'auto:good'},
                    {'fetch_format': 'auto'}
                ]
            )

            url = result.get('secure_url', '')
            size_kb = size_bytes / 1024

            from datetime import datetime, timezone
            return {
                'path': url,
                'size_kb': round(size_kb, 2),
                'uploaded_at': datetime.now(timezone.utc)
            }

        except ImageUploadException:
            raise
        except Exception as e:
            current_app.logger.error(f'Cloudinary upload error: {e}', exc_info=True)
            raise ImageUploadException(f'Upload failed: {str(e)}')

    @staticmethod
    def delete_image(url: str) -> bool:
        """Delete an image from Cloudinary by URL.

        Args:
            url: The Cloudinary secure URL of the image

        Returns:
            True if deleted, False otherwise
        """
        try:
            if not url or 'cloudinary.com' not in url:
                return False

            # Extract public_id from URL
            # URL format: https://res.cloudinary.com/cloud/image/upload/v123/folder/filename.ext
            parts = url.split('/upload/')
            if len(parts) != 2:
                return False

            public_id_with_ext = parts[1]
            # Remove version prefix if present (v1234567/)
            if public_id_with_ext.startswith('v') and '/' in public_id_with_ext:
                public_id_with_ext = public_id_with_ext.split('/', 1)[1]

            # Remove file extension
            public_id = public_id_with_ext.rsplit('.', 1)[0]

            cloudinary.uploader.destroy(public_id)
            return True

        except Exception as e:
            if current_app:
                current_app.logger.error(f'Cloudinary delete error: {e}', exc_info=True)
            return False