"""
Speech API Endpoints - Proxy routes for frontend compatibility

Provides simplified speech endpoints that proxy to the main chat API:
- /api/speech/stt - Speech-to-Text
- /api/speech/tts - Text-to-Speech
"""
import sys
from pathlib import Path
from typing import Optional


from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from backend.speech import transcribe_audio, synthesize_speech
from backend.settings import settings
from datetime import datetime
import uuid


from backend.api.request_response.SpeechReqResp import STTResponse, TTSRequest, TTSResponse
from backend.api.helper.SpeechHelper import validate_audio_file, save_temp_audio_file



# Create router
router = APIRouter(prefix="/api/speech", tags=["speech"])



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
