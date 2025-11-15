"""Audio Service - File Validation, Storage, and Management

This service handles:
- Audio file validation and format checking
- File upload and temporary storage
- Audio file cleanup and lifecycle management
- File path management and organization

Replaces: backend.api.helper.ChatHelper and backend.api.helper.SpeechHelper
"""

import shutil
import time
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from fastapi import UploadFile, HTTPException, status

from backend.utils.base_service import BaseService
from backend.settings import settings


class AudioService(BaseService):
    """Service for audio file operations and management"""

    def __init__(self):
        super().__init__()
        self.service_name = "AudioService"

        # Audio file configuration
        self.allowed_extensions = {".wav", ".mp3", ".ogg", ".m4a", ".webm"}
        self.max_audio_size = 10 * 1024 * 1024  # 10MB
        self.default_cleanup_age_hours = 24

        # Directory paths
        self.audio_out_dir = settings.AUDIO_OUT_DIR
        self.temp_audio_dir = self.audio_out_dir / "temp"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        try:
            self.audio_out_dir.mkdir(parents=True, exist_ok=True)
            self.temp_audio_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Audio directories ensured: {self.audio_out_dir}, {self.temp_audio_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create audio directories: {str(e)}")
            raise ValueError(f"Audio service initialization failed: {str(e)}")

    # File validation
    def validate_audio_file(self, filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """Validate uploaded audio file format and size

        Args:
            filename: Name of the uploaded file
            file_size: Size of the file in bytes

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file passes validation
            - error_message: None if valid, error description if invalid
        """
        if not filename:
            return False, "Filename is required"

        # Check file extension
        try:
            ext = Path(filename).suffix.lower()
            if ext not in self.allowed_extensions:
                return False, (
                    f"Audio type '{ext}' not allowed. "
                    f"Allowed formats: {', '.join(sorted(self.allowed_extensions))}"
                )
        except Exception as e:
            self.logger.warning(f"Error checking file extension for '{filename}': {str(e)}")
            return False, "Invalid filename format"

        # Check file size
        if file_size <= 0:
            return False, "File cannot be empty"

        if file_size > self.max_audio_size:
            max_size_mb = self.max_audio_size / 1024 / 1024
            return False, f"Audio file too large. Maximum size: {max_size_mb:.1f}MB"

        return True, None

    def validate_upload_file(self, file: UploadFile) -> tuple[bool, Optional[str]]:
        """Validate UploadFile object

        Args:
            file: FastAPI UploadFile object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"

        if not file.filename:
            return False, "Filename is required"

        # Get file size (UploadFile doesn't always have size attribute)
        try:
            file_size = file.size if hasattr(file, 'size') and file.size is not None else 0
            # If size not available, we'll validate after reading
            if file_size == 0:
                # Try to get size from file object
                if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
                    current_pos = file.file.tell()
                    file.file.seek(0, 2)  # Seek to end
                    file_size = file.file.tell()
                    file.file.seek(current_pos)  # Reset position
        except Exception:
            file_size = 0  # Will validate during save

        return self.validate_audio_file(file.filename, file_size)

    # File saving operations
    async def save_audio_file(
        self,
        file: UploadFile,
        prefix: str = "upload",
        subfolder: Optional[str] = None
    ) -> Path:
        """Save uploaded audio file to permanent storage

        Args:
            file: Uploaded file object
            prefix: Filename prefix for organization
            subfolder: Optional subfolder within audio directory

        Returns:
            Path to saved file

        Raises:
            HTTPException: If validation fails or save operation fails
        """
        # Validate file first
        is_valid, error_msg = self.validate_upload_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio file: {error_msg}"
            )

        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            ext = Path(file.filename).suffix.lower()
            filename = f"{prefix}_{unique_id}_{timestamp}{ext}"

            # Determine save directory
            if subfolder:
                save_dir = self.audio_out_dir / subfolder
                save_dir.mkdir(parents=True, exist_ok=True)
            else:
                save_dir = self.audio_out_dir

            file_path = save_dir / filename

            # Save file using async file operations
            try:
                content = await file.read()

                # Final size validation if not done earlier
                if len(content) > self.max_audio_size:
                    max_size_mb = self.max_audio_size / 1024 / 1024
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Audio file too large. Maximum size: {max_size_mb:.1f}MB"
                    )

                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)

                self.logger.info(f"Audio file saved: {filename} ({len(content)} bytes)")
                return file_path

            except Exception as e:
                # Clean up partial file if it exists
                if file_path.exists():
                    file_path.unlink(missing_ok=True)
                raise e

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to save audio file '{file.filename}': {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save audio file: {str(e)}"
            )

    async def save_temp_audio_file(
        self,
        file: UploadFile,
        prefix: str = "temp_stt"
    ) -> Path:
        """Save uploaded audio file to temporary storage

        Args:
            file: Uploaded file object
            prefix: Filename prefix for organization

        Returns:
            Path to saved temporary file

        Raises:
            HTTPException: If validation fails or save operation fails
        """
        # Validate file first
        is_valid, error_msg = self.validate_upload_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio file: {error_msg}"
            )

        try:
            # Generate unique filename for temp storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            ext = Path(file.filename).suffix.lower() if file.filename else ".wav"
            filename = f"{prefix}_{unique_id}_{timestamp}{ext}"

            file_path = self.temp_audio_dir / filename

            # Save file
            content = await file.read()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            self.logger.info(f"Temporary audio file saved: {filename} ({len(content)} bytes)")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to save temporary audio file '{file.filename}': {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save temporary audio file: {str(e)}"
            )

    # File management operations
    def cleanup_old_audio_files(
        self,
        max_age_hours: int = None,
        target_directory: Optional[Path] = None,
        pattern: str = "*"
    ) -> Dict[str, Any]:
        """Clean up old audio files

        Args:
            max_age_hours: Maximum age in hours (default: 24)
            target_directory: Directory to clean (default: both main and temp)
            pattern: File pattern to match (default: all files)

        Returns:
            Dictionary with cleanup statistics
        """
        if max_age_hours is None:
            max_age_hours = self.default_cleanup_age_hours

        max_age_seconds = max_age_hours * 3600
        current_time = time.time()

        cleanup_stats = {
            "deleted_files": [],
            "total_deleted": 0,
            "total_size_freed": 0,
            "errors": []
        }

        # Determine directories to clean
        directories_to_clean = []
        if target_directory:
            directories_to_clean = [target_directory]
        else:
            directories_to_clean = [self.audio_out_dir, self.temp_audio_dir]

        for directory in directories_to_clean:
            if not directory.exists():
                continue

            try:
                for file_path in directory.glob(pattern):
                    if not file_path.is_file():
                        continue

                    try:
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age_seconds:
                            file_size = file_path.stat().st_size
                            file_path.unlink()

                            cleanup_stats["deleted_files"].append({
                                "path": str(file_path),
                                "size": file_size,
                                "age_hours": file_age / 3600
                            })
                            cleanup_stats["total_size_freed"] += file_size

                    except Exception as e:
                        error_msg = f"Error deleting {file_path}: {str(e)}"
                        cleanup_stats["errors"].append(error_msg)
                        self.logger.warning(error_msg)

            except Exception as e:
                error_msg = f"Error accessing directory {directory}: {str(e)}"
                cleanup_stats["errors"].append(error_msg)
                self.logger.error(error_msg)

        cleanup_stats["total_deleted"] = len(cleanup_stats["deleted_files"])

        if cleanup_stats["total_deleted"] > 0:
            size_mb = cleanup_stats["total_size_freed"] / 1024 / 1024
            self.logger.info(
                f"Cleaned up {cleanup_stats['total_deleted']} audio files "
                f"({size_mb:.2f}MB freed)"
            )

        return cleanup_stats

    def cleanup_temp_files(self, max_age_hours: int = 1) -> Dict[str, Any]:
        """Clean up temporary audio files with shorter retention

        Args:
            max_age_hours: Maximum age in hours for temp files (default: 1 hour)

        Returns:
            Dictionary with cleanup statistics
        """
        return self.cleanup_old_audio_files(
            max_age_hours=max_age_hours,
            target_directory=self.temp_audio_dir,
            pattern="temp_*"
        )

    # File information and utilities
    def get_audio_file_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get information about an audio file

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            stat = file_path.stat()
            return {
                "path": str(file_path),
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "age_hours": (time.time() - stat.st_mtime) / 3600,
                "is_temp": "temp" in file_path.parts
            }
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return None

    def list_audio_files(
        self,
        include_temp: bool = False,
        max_age_hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List audio files with optional filtering

        Args:
            include_temp: Whether to include temporary files
            max_age_hours: Only include files newer than this age

        Returns:
            List of file information dictionaries
        """
        files = []

        # Main directory
        if self.audio_out_dir.exists():
            for file_path in self.audio_out_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
                    file_info = self.get_audio_file_info(file_path)
                    if file_info:
                        if max_age_hours is None or file_info["age_hours"] <= max_age_hours:
                            files.append(file_info)

        # Temp directory if requested
        if include_temp and self.temp_audio_dir.exists():
            for file_path in self.temp_audio_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
                    file_info = self.get_audio_file_info(file_path)
                    if file_info:
                        if max_age_hours is None or file_info["age_hours"] <= max_age_hours:
                            files.append(file_info)

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified_at"], reverse=True)
        return files

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for audio files

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "main_directory": {
                "path": str(self.audio_out_dir),
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            },
            "temp_directory": {
                "path": str(self.temp_audio_dir),
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            },
            "grand_total": {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }
        }

        # Count main directory
        if self.audio_out_dir.exists():
            for file_path in self.audio_out_dir.glob("*"):
                if file_path.is_file():
                    try:
                        size = file_path.stat().st_size
                        stats["main_directory"]["total_files"] += 1
                        stats["main_directory"]["total_size_bytes"] += size
                    except Exception:
                        pass

        # Count temp directory
        if self.temp_audio_dir.exists():
            for file_path in self.temp_audio_dir.glob("*"):
                if file_path.is_file():
                    try:
                        size = file_path.stat().st_size
                        stats["temp_directory"]["total_files"] += 1
                        stats["temp_directory"]["total_size_bytes"] += size
                    except Exception:
                        pass

        # Calculate MB values and grand totals
        for directory in ["main_directory", "temp_directory"]:
            stats[directory]["total_size_mb"] = round(
                stats[directory]["total_size_bytes"] / 1024 / 1024, 2
            )
            stats["grand_total"]["total_files"] += stats[directory]["total_files"]
            stats["grand_total"]["total_size_bytes"] += stats[directory]["total_size_bytes"]

        stats["grand_total"]["total_size_mb"] = round(
            stats["grand_total"]["total_size_bytes"] / 1024 / 1024, 2
        )

        return stats

    def delete_audio_file(self, file_path: Union[str, Path]) -> bool:
        """Delete a specific audio file

        Args:
            file_path: Path to file to delete

        Returns:
            True if file was deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                self.logger.info(f"Deleted audio file: {path}")
                return True
            else:
                self.logger.warning(f"Audio file not found for deletion: {path}")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting audio file {file_path}: {str(e)}")
            return False