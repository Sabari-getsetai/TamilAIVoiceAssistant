"""Helper functions for chat-related operations, including audio file handling."""

import shutil
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import UploadFile
from backend.settings import settings



ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a"}
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB


def validate_audio_file(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded audio file

    Args:
        filename: Name of the file
        file_size: Size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Audio type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"

    # Check size
    if file_size > MAX_AUDIO_SIZE:
        return False, f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE / 1024 / 1024}MB"

    return True, None


async def save_audio_file(file: UploadFile, prefix: str = "upload") -> Path:
    """
    Save uploaded audio file

    Args:
        file: Uploaded file
        prefix: Filename prefix

    Returns:
        Path to saved file
    """
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename).suffix
    filename = f"{prefix}_{unique_id}_{timestamp}{ext}"

    # Ensure output directory exists
    settings.AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = settings.AUDIO_OUT_DIR / filename

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def cleanup_old_audio_files(max_age_hours: int = 24):
    """
    Clean up old audio files

    Args:
        max_age_hours: Maximum age in hours
    """
    try:
        if not settings.AUDIO_OUT_DIR.exists():
            return

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for file_path in settings.AUDIO_OUT_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    print(f"Cleaned up old audio file: {file_path.name}")

    except Exception as e:
        print(f"Error cleaning up audio files: {e}")