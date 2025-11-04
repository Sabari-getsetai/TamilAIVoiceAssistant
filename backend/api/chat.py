"""
Chat API Endpoints for Tamil AI Voice Assistant

Provides endpoints for:
- Session management (create, get, list, delete)
- Conversation turns (audio → audio, text → text)
- Component testing (STT, TTS, LLM individually)
- Audio file serving
- WebSocket real-time conversation
"""
import sys
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import asyncio
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
    Form,
)
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from backend.settings import settings
from backend.graphs.chat_graph import (
    create_session,
    process_conversation_turn,
    get_session_info,
    get_conversation_history,
    delete_session as delete_chat_session,
    get_session_stats,
    list_active_sessions,
)
from backend.speech import transcribe_audio, synthesize_speech
from backend.models import get_llm, initialize_llm
from backend.rag import get_embedding_model, VectorStore, get_rag_prompt_builder


# Create router
router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Request to create a new chat session"""
    user_id: Optional[str] = None
    language: str = Field(default="ta", description="Language code (ta, en)")
    rag_enabled: bool = Field(default=True, description="Enable RAG retrieval")


class SessionResponse(BaseModel):
    """Response with session information"""
    session_id: str
    user_id: Optional[str]
    language: str
    rag_enabled: bool
    created_at: str
    last_activity: Optional[str] = None
    total_turns: int
    session_duration: Optional[float] = None
    status: str


class ConversationTurnResponse(BaseModel):
    """Response for a conversation turn"""
    success: bool
    session_id: str
    user_text: str
    assistant_text: str
    audio_output_url: Optional[str] = None
    processing_time: Dict[str, float]
    total_time: float
    error: Optional[str] = None


class TextConversationRequest(BaseModel):
    """Request for text-only conversation"""
    text: str
    language: str = "ta"


class TextConversationResponse(BaseModel):
    """Response for text-only conversation"""
    success: bool
    session_id: str
    user_text: str
    assistant_text: str
    processing_time: Dict[str, float]
    total_time: float
    error: Optional[str] = None


class TranscribeResponse(BaseModel):
    """Response for transcription"""
    success: bool
    text: str
    language: str
    confidence: Optional[float] = None
    duration: float


class SynthesizeRequest(BaseModel):
    """Request for speech synthesis"""
    text: str
    language: str = "ta"


class SynthesizeResponse(BaseModel):
    """Response for speech synthesis"""
    success: bool
    audio_url: str
    duration: float
    text_length: int


class GenerateRequest(BaseModel):
    """Request for text generation"""
    text: str
    language: str = "ta"
    use_rag: bool = True


class GenerateResponse(BaseModel):
    """Response for text generation"""
    success: bool
    response_text: str
    context_used: bool
    retrieved_chunks: int
    duration: float


class ConversationHistoryResponse(BaseModel):
    """Response with conversation history"""
    session_id: str
    total_turns: int
    history: List[Dict]


class SessionStatsResponse(BaseModel):
    """Response with session statistics"""
    total_sessions: int
    active_sessions: int
    total_turns: int
    average_session_duration: float
    average_turn_time: float


# ============================================================================
# Utility Functions
# ============================================================================

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


# ============================================================================
# Session Management Endpoints
# ============================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_chat_session(
    request: SessionCreateRequest,
    background_tasks: BackgroundTasks,
) -> SessionResponse:
    """
    Create a new chat session

    Args:
        request: Session creation request

    Returns:
        Session information
    """
    try:
        # Create session
        session_id = create_session(
            user_id=request.user_id,
            language=request.language,
            rag_enabled=request.rag_enabled,
        )

        # Get session info
        session_info = get_session_info(session_id)

        # Schedule cleanup of old audio files
        background_tasks.add_task(cleanup_old_audio_files)

        return SessionResponse(
            session_id=session_id,
            user_id=session_info.get("user_id"),
            language=session_info["language"],
            rag_enabled=session_info["rag_enabled"],
            created_at=session_info["created_at"],
            last_activity=session_info.get("last_activity"),
            total_turns=session_info["total_turns"],
            session_duration=session_info.get("session_duration"),
            status=session_info["status"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {e}")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """
    Get session information

    Args:
        session_id: Session identifier

    Returns:
        Session information
    """
    try:
        session_info = get_session_info(session_id)

        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            session_id=session_id,
            user_id=session_info.get("user_id"),
            language=session_info["language"],
            rag_enabled=session_info["rag_enabled"],
            created_at=session_info["created_at"],
            last_activity=session_info.get("last_activity"),
            total_turns=session_info["total_turns"],
            session_duration=session_info.get("session_duration"),
            status=session_info["status"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session: {e}")


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions() -> List[SessionResponse]:
    """
    List all active sessions

    Returns:
        List of active sessions
    """
    try:
        sessions = list_active_sessions()

        return [
            SessionResponse(
                session_id=sid,
                user_id=info.get("user_id"),
                language=info["language"],
                rag_enabled=info["rag_enabled"],
                created_at=info["created_at"],
                last_activity=info.get("last_activity"),
                total_turns=info["total_turns"],
                session_duration=info.get("session_duration"),
                status=info["status"],
            )
            for sid, info in sessions.items()
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {e}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> JSONResponse:
    """
    Delete a chat session

    Args:
        session_id: Session identifier

    Returns:
        Deletion confirmation
    """
    try:
        success = delete_chat_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Session {session_id} deleted successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {e}")


@router.get("/sessions/{session_id}/history", response_model=ConversationHistoryResponse)
async def get_history(session_id: str) -> ConversationHistoryResponse:
    """
    Get conversation history for a session

    Args:
        session_id: Session identifier

    Returns:
        Conversation history
    """
    try:
        history = get_conversation_history(session_id)

        if history is None:
            raise HTTPException(status_code=404, detail="Session not found")

        return ConversationHistoryResponse(
            session_id=session_id,
            total_turns=len(history),
            history=history,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting history: {e}")


@router.get("/stats", response_model=SessionStatsResponse)
async def get_stats() -> SessionStatsResponse:
    """
    Get global session statistics

    Returns:
        Session statistics
    """
    try:
        stats = get_session_stats()

        return SessionStatsResponse(
            total_sessions=stats["total_sessions"],
            active_sessions=stats["active_sessions"],
            total_turns=stats["total_turns"],
            average_session_duration=stats["average_session_duration"],
            average_turn_time=stats["average_turn_time"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {e}")


# ============================================================================
# Conversation Endpoints
# ============================================================================

@router.post("/sessions/{session_id}/turn", response_model=ConversationTurnResponse)
async def process_turn(
    session_id: str,
    audio: UploadFile = File(...),
    language: str = Form(default="ta"),
) -> ConversationTurnResponse:
    """
    Process a conversation turn (audio → audio)

    Args:
        session_id: Session identifier
        audio: Audio file with user speech
        language: Language code

    Returns:
        Conversation turn result
    """
    audio_path = None
    
    try:
        # Validate session exists
        session_info = get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")

        # Read and validate audio file
        content = await audio.read()
        file_size = len(content)
        await audio.seek(0)

        is_valid, error_msg = validate_audio_file(audio.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Save audio file
        audio_path = await save_audio_file(audio, prefix="input")

        # Process conversation turn
        start_time = time.time()
        result = process_conversation_turn(
            session_id=session_id,
            audio_input_path=str(audio_path),
            language=language,
        )
        total_time = time.time() - start_time

        # Build response
        audio_url = None
        if result.get("audio_output_path"):
            audio_filename = Path(result["audio_output_path"]).name
            audio_url = f"/chat/audio/{audio_filename}"

        return ConversationTurnResponse(
            success=result["status"] == "completed",
            session_id=session_id,
            user_text=result.get("user_text", ""),
            assistant_text=result.get("assistant_text", ""),
            audio_output_url=audio_url,
            processing_time=result.get("processing_time", {}),
            total_time=total_time,
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing turn: {e}")
    finally:
        # Clean up input audio file
        if audio_path and audio_path.exists():
            try:
                audio_path.unlink()
            except:
                pass


@router.post("/sessions/{session_id}/text", response_model=TextConversationResponse)
async def process_text_turn(
    session_id: str,
    request: TextConversationRequest,
) -> TextConversationResponse:
    """
    Process a text-only conversation turn

    Args:
        session_id: Session identifier
        request: Text conversation request

    Returns:
        Text conversation result
    """
    try:
        # Validate session exists
        session_info = get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")

        # Process with text input (no audio)
        start_time = time.time()
        result = process_conversation_turn(
            session_id=session_id,
            text_input=request.text,
            language=request.language,
        )
        total_time = time.time() - start_time

        return TextConversationResponse(
            success=result["status"] == "completed",
            session_id=session_id,
            user_text=result.get("user_text", ""),
            assistant_text=result.get("assistant_text", ""),
            processing_time=result.get("processing_time", {}),
            total_time=total_time,
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text turn: {e}")


# ============================================================================
# Component Testing Endpoints
# ============================================================================

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(...),
    language: str = Form(default="ta"),
) -> TranscribeResponse:
    """
    Transcribe audio to text (STT only)

    Args:
        audio: Audio file
        language: Language code

    Returns:
        Transcription result
    """
    audio_path = None
    
    try:
        # Read and validate audio file
        content = await audio.read()
        file_size = len(content)
        await audio.seek(0)

        is_valid, error_msg = validate_audio_file(audio.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Save audio file
        audio_path = await save_audio_file(audio, prefix="transcribe")

        # Transcribe
        start_time = time.time()
        text = transcribe_audio(str(audio_path), language=language)
        duration = time.time() - start_time

        return TranscribeResponse(
            success=True,
            text=text,
            language=language,
            confidence=None,  # Not available from current STT
            duration=duration,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {e}")
    finally:
        # Clean up audio file
        if audio_path and audio_path.exists():
            try:
                audio_path.unlink()
            except:
                pass


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(request: SynthesizeRequest) -> SynthesizeResponse:
    """
    Synthesize speech from text (TTS only)

    Args:
        request: Synthesis request

    Returns:
        Synthesis result
    """
    try:
        # Synthesize speech
        start_time = time.time()
        
        # Create output path
        from datetime import datetime
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"tts_{unique_id}_{timestamp}.wav"
        settings.AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
        audio_path = settings.AUDIO_OUT_DIR / filename
        
        # Synthesize speech (note: synthesize_speech doesn't take language param)
        audio_data = synthesize_speech(
            text=request.text,
            output_path=str(audio_path)
        )
        duration = time.time() - start_time
        
        if audio_data is None:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")

        # Build audio URL
        audio_filename = Path(audio_path).name
        audio_url = f"/chat/audio/{audio_filename}"

        return SynthesizeResponse(
            success=True,
            audio_url=audio_url,
            duration=duration,
            text_length=len(request.text),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {e}")


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Generate text response (LLM only)

    Args:
        request: Generation request

    Returns:
        Generation result
    """
    try:
        start_time = time.time()

        # Get LLM model
        llm = get_llm()
        if not llm.is_loaded():
            initialize_llm()

        # Optionally use RAG
        context = ""
        retrieved_chunks = 0

        if request.use_rag:
            try:
                # Get embedding model and vector store
                embedding_model = get_embedding_model()
                if not embedding_model.is_loaded():
                    embedding_model.load()

                vector_store = VectorStore(
                    embedding_dimension=embedding_model.get_dimension(),
                    store_name="default"
                )

                if vector_store.load():
                    # Retrieve relevant chunks
                    query_embedding = embedding_model.embed_text(request.text)
                    results = vector_store.search(query_embedding, k=3)
                    
                    if results:
                        retrieved_chunks = len(results)
                        context = "\n\n".join([doc.text for doc, _ in results])

            except Exception as e:
                print(f"RAG retrieval failed: {e}")

        # Build prompt
        if context:
            prompt_builder = get_rag_prompt_builder()
            # Convert context string to document list format
            context_docs = [{"content": context, "metadata": {}}]
            prompt = prompt_builder.build_with_context(
                question=request.text,
                context_documents=context_docs,
                conversation_history=""
            )
        else:
            prompt = request.text

        # Generate response
        response_text = llm.generate(prompt)
        duration = time.time() - start_time

        return GenerateResponse(
            success=True,
            response_text=response_text,
            context_used=bool(context),
            retrieved_chunks=retrieved_chunks,
            duration=duration,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")


# ============================================================================
# Audio File Serving
# ============================================================================

@router.get("/audio/{filename}")
async def get_audio(filename: str) -> FileResponse:
    """
    Download audio file

    Args:
        filename: Audio filename

    Returns:
        Audio file
    """
    try:
        file_path = settings.AUDIO_OUT_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")

        return FileResponse(
            path=str(file_path),
            media_type="audio/wav",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving audio: {e}")


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time conversation

    Args:
        websocket: WebSocket connection
        session_id: Session identifier
    """
    await websocket.accept()
    
    try:
        # Validate session exists
        session_info = get_session_info(session_id)
        if not session_info:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Session not found"},
                "timestamp": datetime.now().isoformat(),
            })
            await websocket.close()
            return

        # Send connection confirmation
        await websocket.send_json({
            "type": "status",
            "data": {
                "message": "Connected",
                "session_id": session_id,
            },
            "timestamp": datetime.now().isoformat(),
        })

        # Message loop
        while True:
            # Receive message
            message = await websocket.receive_json()
            
            message_type = message.get("type")
            
            if message_type == "text":
                # Process text message
                try:
                    text = message.get("data", {}).get("text", "")
                    language = message.get("data", {}).get("language", "ta")
                    
                    # Process turn
                    result = process_conversation_turn(
                        session_id=session_id,
                        text_input=text,
                        language=language,
                    )
                    
                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "data": {
                            "user_text": result.get("user_text", ""),
                            "assistant_text": result.get("assistant_text", ""),
                            "processing_time": result.get("processing_time", {}),
                        },
                        "timestamp": datetime.now().isoformat(),
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                        "timestamp": datetime.now().isoformat(),
                    })
            
            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                    "data": {},
                    "timestamp": datetime.now().isoformat(),
                })
            
            elif message_type == "close":
                # Close connection
                break

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
                "timestamp": datetime.now().isoformat(),
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
