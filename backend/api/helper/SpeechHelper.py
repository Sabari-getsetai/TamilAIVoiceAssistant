"""Helper functions for speech-related operations, including audio file validation and temporary storage."""
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import UploadFile
from backend.settings import settings



ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".webm"}
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB


def validate_audio_file(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
    """Validate uploaded audio file"""
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Audio type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"

    # Check size
    if file_size > MAX_AUDIO_SIZE:
        return False, f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE / 1024 / 1024}MB"

    return True, None


async def save_temp_audio_file(file: UploadFile) -> Path:
    """Save uploaded audio file temporarily"""
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename).suffix if file.filename else ".wav"
    filename = f"temp_stt_{unique_id}_{timestamp}{ext}"

    # Ensure temp directory exists
    temp_dir = settings.AUDIO_OUT_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / filename

    # Save file
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return file_path