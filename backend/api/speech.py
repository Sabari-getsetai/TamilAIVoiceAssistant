"""
Speech API Endpoints - Proxy routes for frontend compatibility

Provides simplified speech endpoints that proxy to the main chat API:
- /api/speech/stt - Speech-to-Text
- /api/speech/tts - Text-to-Speech
"""
import sys
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.speech import transcribe_audio, synthesize_speech
from backend.settings import settings
from datetime import datetime
import uuid

# Create router
router = APIRouter(prefix="/api/speech", tags=["speech"])


# ============================================================================
# Request/Response Models
# ============================================================================

class STTResponse(BaseModel):
    """Speech-to-Text response"""
    text: str
    confidence: Optional[float] = None


class TTSRequest(BaseModel):
    """Text-to-Speech request"""
    text: str
    language: str = "ta"


class TTSResponse(BaseModel):
    """Text-to-Speech response"""
    audio_url: str


# ============================================================================
# Utility Functions
# ============================================================================

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


# ============================================================================
# Speech API Endpoints
# ============================================================================

@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = Form(default="ta"),
) -> STTResponse:
    """
    Convert speech to text
    
    Args:
        audio: Audio file with speech
        language: Language code (ta, en)
        
    Returns:
        Transcribed text
    """
    audio_path = None
    
    try:
        # Read and validate audio file
        content = await audio.read()
        file_size = len(content)
        await audio.seek(0)

        is_valid, error_msg = validate_audio_file(audio.filename or "audio.wav", file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Save audio file temporarily
        audio_path = await save_temp_audio_file(audio)

        # Transcribe audio
        text = transcribe_audio(str(audio_path), language=language)
        
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")

        return STTResponse(
            text=text.strip(),
            confidence=None  # Not available from current STT implementation
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {e}")
    finally:
        # Clean up temporary file
        if audio_path and audio_path.exists():
            try:
                audio_path.unlink()
            except:
                pass


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest) -> TTSResponse:
    """
    Convert text to speech
    
    Args:
        request: Text to synthesize
        
    Returns:
        Audio file URL
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Create output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"tts_{unique_id}_{timestamp}.wav"
        settings.AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
        audio_path = settings.AUDIO_OUT_DIR / filename
        
        # Synthesize speech
        audio_data = synthesize_speech(
            text=request.text.strip(),
            output_path=str(audio_path)
        )
        
        if audio_data is None:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")

        # Return audio URL (relative to chat API)
        audio_url = f"/chat/audio/{filename}"

        return TTSResponse(audio_url=audio_url)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {e}")
