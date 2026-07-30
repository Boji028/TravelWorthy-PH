"""Image upload service using Cloudinary for cloud storage."""
import os
import re
from typing import Optional
import cloudinary
import cloudinary.uploader
from flask import current_app


class ImageUploadException(Exception):
    """Raised when an image upload fails."""

    pass


# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


class ImageUploadService:
    """Handles image uploads to Cloudinary."""

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_IMAGE_SIZE_MB = 25
    MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
    MAX_PDF_SIZE_MB = 5
    MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

    @staticmethod
    def _allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ImageUploadService.ALLOWED_EXTENSIONS

    @staticmethod
    def _check_magic_bytes(file) -> bool:
        """Verify file starts with a known image magic-byte sequence."""
        header = file.read(12)
        file.seek(0)
        return (
            header[:3] == b"\xff\xd8\xff"
            or header[:8] == b"\x89PNG\r\n\x1a\n"  # JPEG/JPG
            or header[:6] in (b"GIF87a", b"GIF89a")  # PNG
            or (header[:4] == b"RIFF" and header[8:12] == b"WEBP")  # GIF  # WEBP
        )

    @staticmethod
    def upload_and_compress(file, prefix: str = "img") -> dict:
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
            raise ImageUploadException("No file provided.")

        if not ImageUploadService._allowed_file(file.filename):
            raise ImageUploadException(f'Invalid file type. Allowed: {", ".join(ImageUploadService.ALLOWED_EXTENSIONS)}')

        if not ImageUploadService._check_magic_bytes(file):
            raise ImageUploadException("File content does not match a supported image format.")

        # Check file size
        file.seek(0, 2)  # Seek to end
        size_bytes = file.tell()
        file.seek(0)  # Reset

        if size_bytes > ImageUploadService.MAX_IMAGE_SIZE_BYTES:
            raise ImageUploadException(f"File too large. Maximum size is {ImageUploadService.MAX_IMAGE_SIZE_MB}MB.")

        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file, folder=f"travelworthyph/{prefix}", transformation=[{"quality": "auto:best"}, {"fetch_format": "auto"}]
            )

            url = result.get("secure_url", "")
            size_kb = size_bytes / 1024

            from datetime import datetime, timezone

            return {"path": url, "size_kb": round(size_kb, 2), "uploaded_at": datetime.now(timezone.utc)}

        except ImageUploadException:
            raise
        except Exception as e:
            current_app.logger.error(f"Cloudinary upload error: {e}", exc_info=True)
            raise ImageUploadException(f"Upload failed: {str(e)}")

    @staticmethod
    def upload_pdf(file, prefix: str = "pdf") -> dict:
        """Upload a PDF to Cloudinary as a raw file.

        Images go through upload_and_compress(); PDFs (and any other
        non-image document) go through here instead, using
        resource_type="raw" since Cloudinary's image pipeline (transforms,
        compression) doesn't apply to them.

        Args:
            file: FileStorage object from Flask
            prefix: Folder/prefix for organizing uploads (e.g. 'visa')

        Returns:
            dict with 'path' (full URL), 'size_kb', 'uploaded_at'

        Raises:
            ImageUploadException: if validation or upload fails
        """
        if not file or not file.filename:
            raise ImageUploadException("No file provided.")

        if not file.filename.lower().endswith(".pdf"):
            raise ImageUploadException("Only PDF files are allowed.")

        # Check file size
        file.seek(0, 2)  # Seek to end
        size_bytes = file.tell()
        file.seek(0)  # Reset

        if size_bytes > ImageUploadService.MAX_PDF_SIZE_BYTES:
            raise ImageUploadException(f"File too large. Maximum size is {ImageUploadService.MAX_PDF_SIZE_MB}MB.")

        try:
            result = cloudinary.uploader.upload(file, folder=f"travelworthyph/{prefix}", resource_type="raw")

            url = result.get("secure_url", "")
            size_kb = size_bytes / 1024

            from datetime import datetime, timezone

            return {"path": url, "size_kb": round(size_kb, 2), "uploaded_at": datetime.now(timezone.utc)}

        except ImageUploadException:
            raise
        except Exception as e:
            current_app.logger.error(f"Cloudinary PDF upload error: {e}", exc_info=True)
            raise ImageUploadException(f"Upload failed: {str(e)}")

    @staticmethod
    def delete_image(url: str, resource_type: str = "image") -> bool:
        """Delete an asset from Cloudinary by URL.

        Args:
            url: The Cloudinary secure URL of the asset
            resource_type: "image" (default) or "raw" — must match the type
                the asset was uploaded with (upload_and_compress uses
                "image", upload_pdf uses "raw"), or Cloudinary won't find it

        Returns:
            True if deleted, False otherwise
        """
        try:
            if not url or "cloudinary.com" not in url:
                return False

            # Extract public_id from URL
            # URL format: https://res.cloudinary.com/cloud/image/upload/v123/folder/filename.ext
            parts = url.split("/upload/")
            if len(parts) != 2:
                return False

            # Strip optional transformation segments and version prefix
            # e.g. "q_auto,f_auto/v1234567/folder/file.jpg" → "folder/file.jpg"
            public_id_with_ext = re.sub(r"^([^/]+/)*v\d+/", "", parts[1])

            # Remove file extension
            public_id = public_id_with_ext.rsplit(".", 1)[0]

            result = cloudinary.uploader.destroy(public_id, resource_type)
            return result.get("result") == "ok"

        except Exception as e:
            try:
                current_app.logger.error(f"Cloudinary delete error: {e}", exc_info=True)
            except RuntimeError:
                # Called outside app context (e.g., from a management script)
                import logging

                logging.getLogger(__name__).error(f"Cloudinary delete error: {e}")
            return False
