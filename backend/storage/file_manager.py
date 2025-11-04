"""
File management utilities for Tamil AI Voice Assistant.

This module provides high-level file management operations:
- Document upload and organization
- Audio file handling
- User-specific file isolation
- File type validation and processing
"""

import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, BinaryIO
from pathlib import Path
import logging

from .minio_client import (
    upload_file,
    download_file,
    delete_file,
    get_presigned_url,
    DOCUMENTS_BUCKET,
    AUDIO_BUCKET
)

logger = logging.getLogger(__name__)

# File type configurations
ALLOWED_DOCUMENT_TYPES = ["pdf", "docx", "txt", "md", "rtf"]
ALLOWED_AUDIO_TYPES = ["wav", "mp3", "m4a", "webm", "ogg"]
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))


class FileManager:
    """High-level file management for documents and audio files."""

    def __init__(self):
        self.max_file_size = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes

    def generate_object_key(
        self,
        user_id: str,
        file_type: str,
        filename: str,
        session_id: Optional[str] = None,
        subfolder: Optional[str] = None
    ) -> str:
        """
        Generate a unique object key for MinIO storage.

        Args:
            user_id: User identifier
            file_type: Type of file ('document' or 'audio')
            filename: Original filename
            session_id: Optional session ID for grouping
            subfolder: Optional subfolder (e.g., 'input', 'output', 'refined')

        Returns:
            str: Unique object key
        """
        # Generate unique filename to avoid conflicts
        file_extension = Path(filename).suffix
        unique_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_extension}"

        # Build key path
        parts = ["users", user_id, file_type]

        if session_id:
            parts.extend(["sessions", session_id])

        if subfolder:
            parts.append(subfolder)

        parts.append(unique_name)

        return "/".join(parts)

    def validate_file(self, filename: str, file_size: int, file_type: str) -> Dict[str, Any]:
        """
        Validate uploaded file.

        Args:
            filename: Original filename
            file_size: File size in bytes
            file_type: Expected file type ('document' or 'audio')

        Returns:
            dict: Validation result with 'valid' boolean and 'errors' list
        """
        errors = []

        # Check file size
        if file_size > self.max_file_size:
            errors.append(f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({MAX_UPLOAD_SIZE_MB}MB)")

        # Check file extension
        file_extension = Path(filename).suffix.lower().lstrip('.')

        if file_type == "document":
            allowed_types = ALLOWED_DOCUMENT_TYPES
        elif file_type == "audio":
            allowed_types = ALLOWED_AUDIO_TYPES
        else:
            errors.append(f"Invalid file type: {file_type}")
            allowed_types = []

        if file_extension not in allowed_types:
            errors.append(f"File type '.{file_extension}' not allowed. Allowed types: {', '.join(allowed_types)}")

        # Check filename
        if not filename or len(filename.strip()) == 0:
            errors.append("Filename cannot be empty")

        if len(filename) > 255:
            errors.append("Filename too long (max 255 characters)")

        # Check for potentially dangerous filenames
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\0"]
        if any(char in filename for char in dangerous_chars):
            errors.append("Filename contains invalid characters")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_extension": file_extension,
            "content_type": mimetypes.guess_type(filename)[0] or "application/octet-stream"
        }

    async def upload_document(
        self,
        user_id: str,
        filename: str,
        file_data: BinaryIO,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a document file.

        Args:
            user_id: User identifier
            filename: Original filename
            file_data: File binary data
            session_id: Optional session ID for grouping
            metadata: Optional additional metadata

        Returns:
            dict: Upload result with success status and file information
        """
        try:
            # Get file size
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)

            # Validate file
            validation = self.validate_file(filename, file_size, "document")
            if not validation["valid"]:
                return {
                    "success": False,
                    "errors": validation["errors"]
                }

            # Generate object key
            object_key = self.generate_object_key(
                user_id=user_id,
                file_type="documents",
                filename=filename,
                session_id=session_id
            )

            # Prepare metadata
            file_metadata = {
                "user_id": user_id,
                "original_filename": filename,
                "file_type": validation["file_extension"],
                "upload_timestamp": str(int(datetime.utcnow().timestamp())),
                "file_size": str(file_size)
            }

            if session_id:
                file_metadata["session_id"] = session_id

            if metadata:
                file_metadata.update(metadata)

            # Upload to MinIO
            success = upload_file(
                bucket_name=DOCUMENTS_BUCKET,
                object_name=object_key,
                file_data=file_data,
                content_type=validation["content_type"],
                metadata=file_metadata
            )

            if success:
                return {
                    "success": True,
                    "object_key": object_key,
                    "filename": filename,
                    "file_size": file_size,
                    "content_type": validation["content_type"],
                    "bucket": DOCUMENTS_BUCKET
                }
            else:
                return {
                    "success": False,
                    "errors": ["Failed to upload file to storage"]
                }

        except Exception as e:
            logger.error(f"Error uploading document {filename} for user {user_id}: {e}")
            return {
                "success": False,
                "errors": [f"Upload failed: {str(e)}"]
            }

    async def upload_audio(
        self,
        user_id: str,
        filename: str,
        file_data: BinaryIO,
        audio_type: str,
        session_id: Optional[str] = None,
        duration: Optional[float] = None,
        sample_rate: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload an audio file.

        Args:
            user_id: User identifier
            filename: Original filename
            file_data: File binary data
            audio_type: Audio type ('input', 'output', 'refined')
            session_id: Optional session ID
            duration: Audio duration in seconds
            sample_rate: Audio sample rate
            metadata: Optional additional metadata

        Returns:
            dict: Upload result with success status and file information
        """
        try:
            # Get file size
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)

            # Validate file
            validation = self.validate_file(filename, file_size, "audio")
            if not validation["valid"]:
                return {
                    "success": False,
                    "errors": validation["errors"]
                }

            # Generate object key
            object_key = self.generate_object_key(
                user_id=user_id,
                file_type="audio",
                filename=filename,
                session_id=session_id,
                subfolder=audio_type
            )

            # Prepare metadata
            file_metadata = {
                "user_id": user_id,
                "original_filename": filename,
                "audio_type": audio_type,
                "file_type": validation["file_extension"],
                "upload_timestamp": str(int(datetime.utcnow().timestamp())),
                "file_size": str(file_size)
            }

            if session_id:
                file_metadata["session_id"] = session_id

            if duration:
                file_metadata["duration"] = str(duration)

            if sample_rate:
                file_metadata["sample_rate"] = str(sample_rate)

            if metadata:
                file_metadata.update(metadata)

            # Upload to MinIO
            success = upload_file(
                bucket_name=AUDIO_BUCKET,
                object_name=object_key,
                file_data=file_data,
                content_type=validation["content_type"],
                metadata=file_metadata
            )

            if success:
                return {
                    "success": True,
                    "object_key": object_key,
                    "filename": filename,
                    "file_size": file_size,
                    "content_type": validation["content_type"],
                    "bucket": AUDIO_BUCKET,
                    "audio_type": audio_type,
                    "duration": duration,
                    "sample_rate": sample_rate
                }
            else:
                return {
                    "success": False,
                    "errors": ["Failed to upload audio file to storage"]
                }

        except Exception as e:
            logger.error(f"Error uploading audio {filename} for user {user_id}: {e}")
            return {
                "success": False,
                "errors": [f"Audio upload failed: {str(e)}"]
            }

    async def get_download_url(
        self,
        object_key: str,
        bucket_name: str,
        expires_minutes: int = 15
    ) -> Optional[str]:
        """
        Get a pre-signed download URL for a file.

        Args:
            object_key: MinIO object key
            bucket_name: Bucket name
            expires_minutes: URL expiration time in minutes

        Returns:
            str: Pre-signed download URL or None if failed
        """
        try:
            return get_presigned_url(
                bucket_name=bucket_name,
                object_name=object_key,
                expires=timedelta(minutes=expires_minutes),
                method="GET"
            )
        except Exception as e:
            logger.error(f"Error generating download URL for {object_key}: {e}")
            return None

    async def delete_file(self, object_key: str, bucket_name: str) -> bool:
        """
        Delete a file from storage.

        Args:
            object_key: MinIO object key
            bucket_name: Bucket name

        Returns:
            bool: True if deletion successful
        """
        try:
            return delete_file(bucket_name, object_key)
        except Exception as e:
            logger.error(f"Error deleting file {object_key}: {e}")
            return False

    async def cleanup_expired_audio(self, hours: int = 24) -> int:
        """
        Clean up expired audio files.

        Args:
            hours: Delete audio files older than this many hours

        Returns:
            int: Number of files deleted
        """
        # This would be implemented with a background task
        # For now, rely on MinIO lifecycle policies
        logger.info(f"Audio cleanup triggered (files older than {hours} hours)")
        return 0

    def get_user_storage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get storage statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            dict: Storage statistics
        """
        # This would query MinIO to get user storage usage
        # For now, return placeholder data
        return {
            "documents": {
                "count": 0,
                "total_size_bytes": 0
            },
            "audio": {
                "count": 0,
                "total_size_bytes": 0
            },
            "total_size_bytes": 0
        }