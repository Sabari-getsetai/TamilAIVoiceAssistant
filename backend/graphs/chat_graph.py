"""
Conversational Chat Pipeline using LangGraph for Tamil AI Voice Assistant

This module implements a complete conversation workflow that integrates:
- Speech-to-Text (STT) processing
- RAG document retrieval
- LLM response generation
- Text-to-Speech (TTS) synthesis
- Conversation history management
- Session management

The workflow uses LangGraph to orchestrate the conversation flow with proper
error handling and state management.
"""

import os
import sys
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, TypedDict, Union
import asyncio
import logging
import numpy as np


from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from backend.settings import settings
from backend.speech import (
    initialize_stt, initialize_tts,
    get_stt_engine, get_tts_engine,
    transcribe_audio, synthesize_speech
)
from backend.storage.file_manager import FileManager
from backend.services.tier_service import get_tier_for_session, get_retention_for_session
from backend.models import get_llm, initialize_llm
from backend.rag import (
    get_embedding_model, VectorStore,
    get_rag_prompt_builder
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FileManager for MinIO uploads
file_manager = FileManager()

async def upload_tts_audio_to_minio(
    audio_data: Any,  # numpy.ndarray
    session_id: str,
    filename: str,
    user_id: str = "anonymous"
) -> Optional[str]:
    """
    Upload TTS-generated audio to MinIO.

    Args:
        audio_data: TTS audio data as numpy array
        session_id: Session identifier
        filename: Filename for the audio
        user_id: User identifier (default 'anonymous')

    Returns:
        MinIO object key if successful, None if failed
    """
    try:
        import io
        import wave

        # Convert numpy array to WAV bytes (TTS usually outputs at 24kHz for Chirp3 HD)
        sample_rate = 24000  # Google Cloud TTS Chirp3 HD sample rate
        duration = len(audio_data) / sample_rate

        # Convert float32 to int16 PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        wav_bytes = wav_buffer.getvalue()
        wav_buffer.close()

        # Detect user tier for retention policy
        user_tier = await get_tier_for_session(session_id)
        retention_hours = await get_retention_for_session(session_id)

        # Create BytesIO object for file upload
        audio_file = io.BytesIO(wav_bytes)

        # Add tier-based metadata
        tier_metadata = {
            "user_tier": user_tier,
            "retention_hours": str(retention_hours),
            "retention_policy": f"{retention_hours}h_from_upload",
            "audio_source": "tts_output"
        }

        # Upload to MinIO
        result = await file_manager.upload_audio(
            user_id=user_id,
            filename=filename,
            file_data=audio_file,
            audio_type="output",
            session_id=session_id,
            duration=duration,
            sample_rate=sample_rate,
            metadata=tier_metadata
        )

        if result.get("success"):
            object_key = result.get("object_key")
            logger.info(f"✅ TTS audio uploaded to MinIO: {object_key} (size: {len(wav_bytes)} bytes, {duration:.2f}s)")

            # Save local debug copy if enabled
            if settings.ENABLE_LOCAL_AUDIO_DEBUG:
                debug_dir = settings.AUDIO_OUT_DIR / "debug_output"
                debug_dir.mkdir(parents=True, exist_ok=True)
                debug_file = debug_dir / filename

                with open(debug_file, 'wb') as f:
                    f.write(wav_bytes)
                logger.info(f"🐛 DEBUG: TTS local copy saved to {debug_file}")

            return object_key
        else:
            logger.error(f"❌ Failed to upload TTS audio to MinIO: {result.get('errors', 'Unknown error')}")
            return None

    except Exception as e:
        logger.error(f"❌ Error uploading TTS audio to MinIO: {e}")
        return None


class ChatState(TypedDict):
    """
    State schema for conversational chat pipeline
    
    Manages the complete conversation state including:
    - Session information
    - Current turn data
    - Conversation history
    - RAG context
    - Processing status
    - Performance metrics
    """
    
    # Session management
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    
    # Current turn input/output
    audio_input: Optional[bytes]
    audio_input_path: Optional[str]
    user_text: str
    assistant_text: str
    audio_output: Optional[bytes]
    audio_output_path: Optional[str]
    
    # Conversation history
    conversation_history: List[Dict[str, Any]]
    
    # RAG context
    retrieved_documents: List[Dict[str, Any]]
    context_used: str
    rag_enabled: bool
    
    # Processing status
    current_step: str
    error_message: Optional[str]
    processing_time: Dict[str, float]
    
    # Configuration
    language: str
    max_history_turns: int
    
    # Metadata
    total_turns: int
    session_duration: float


# Helper function to convert database session to ChatState format
def _convert_db_session_to_chat_state(session_data: Dict[str, Any], history: List[Dict[str, Any]]) -> ChatState:
    """
    Convert database session format to ChatState format.
    
    Args:
        session_data: Session data from database
        history: Conversation history from database
        
    Returns:
        ChatState dictionary
    """
    from datetime import datetime
    
    created_at = datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00"))
    last_activity = datetime.fromisoformat(session_data["last_activity"].replace("Z", "+00:00"))
    
    metadata = session_data.get("session_metadata", {})
    
    return {
        # Session management
        "session_id": session_data["session_id"],
        "user_id": session_data["user_id"],
        "created_at": created_at,
        "last_activity": last_activity,
        
        # Current turn (empty for existing sessions)
        "audio_input": None,
        "audio_input_path": None,
        "user_text": "",
        "assistant_text": "",
        "audio_output": None,
        "audio_output_path": None,
        
        # Conversation history
        "conversation_history": history,
        
        # RAG context
        "retrieved_documents": [],
        "context_used": "",
        "rag_enabled": session_data["rag_enabled"],
        
        # Processing status
        "current_step": metadata.get("current_step", "ready"),
        "error_message": metadata.get("error_message"),
        "processing_time": metadata.get("processing_time", {}),
        
        # Configuration
        "language": session_data["language"],
        "max_history_turns": settings.CHAT_MAX_HISTORY_TURNS,
        
        # Metadata
        "total_turns": session_data["total_turns"],
        "session_duration": session_data["duration_seconds"]
    }


# Import database session manager
from backend.services.session_service import get_session_manager
from backend.database.connection import get_db

# Global session manager instance
_session_manager = None

async def get_or_create_session_manager():
    """Get or create global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = await get_session_manager()
    return _session_manager


def transcribe_node(state: ChatState) -> ChatState:
    """
    Node: Transcribe audio input to text using STT
    
    Args:
        state: Current chat state
        
    Returns:
        Updated state with user_text
    """
    start_time = time.time()
    state["current_step"] = "transcribing"
    
    try:
        logger.info(f"Transcribing audio for session {state['session_id']}")
        
        # Check if we have audio input
        if not state.get("audio_input_path") and not state.get("audio_input"):
            raise ValueError("No audio input provided")
        
        # Initialize STT if needed
        if not initialize_stt():
            raise RuntimeError("Failed to initialize STT engine")
        
        # Transcribe audio
        if state.get("audio_input_path"):
            # Transcribe from file path
            user_text = transcribe_audio(
                state["audio_input_path"],
                language=state["language"]
            )
        else:
            # Transcribe from audio bytes (would need to save to temp file)
            # For now, assume we have a file path
            raise NotImplementedError("Direct audio bytes transcription not implemented yet")
        
        if not user_text.strip():
            raise ValueError("No speech detected in audio")
        
        state["user_text"] = user_text.strip()
        state["error_message"] = None
        
        logger.info(f"Transcription successful: {user_text[:50]}...")
        
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(error_msg)
        state["error_message"] = error_msg
        state["user_text"] = ""
    
    # Record processing time
    state["processing_time"]["transcribe"] = time.time() - start_time
    
    return state


def retrieve_node(state: ChatState) -> ChatState:
    """
    Node: Retrieve relevant documents using RAG pipeline
    
    Args:
        state: Current chat state
        
    Returns:
        Updated state with retrieved_documents and context_used
    """
    start_time = time.time()
    state["current_step"] = "retrieving"
    
    try:
        logger.info(f"Retrieving documents for session {state['session_id']}")
        
        # Skip RAG if disabled or no user text
        if not state["rag_enabled"] or not state["user_text"]:
            state["retrieved_documents"] = []
            state["context_used"] = ""
            logger.info("RAG disabled or no user text, skipping retrieval")
            return state
        
        # Import RAG components
        from backend.rag.vectorstore import VectorStore
        from backend.rag.embeddings import get_embedding_model

        # Initialize embeddings and vectorstore
        embeddings = get_embedding_model()
        vectorstore = VectorStore(
            embedding_dimension=384,  # paraphrase-multilingual-MiniLM-L12-v2 dimension
            store_name="default"
        )

        # Check if vectorstore exists and has documents
        if not vectorstore.index_exists():
            logger.warning("FAISS vectorstore not found, skipping RAG retrieval")
            state["retrieved_documents"] = []
            state["context_used"] = ""
            return state

        # Load the vectorstore
        if not vectorstore.load_index():
            logger.warning("Failed to load FAISS vectorstore, skipping RAG retrieval")
            state["retrieved_documents"] = []
            state["context_used"] = ""
            return state

        # Perform similarity search
        retrieval_k = getattr(settings, 'RETRIEVAL_K', 3)
        docs = vectorstore.similarity_search(
            state["user_text"],
            k=retrieval_k,
            embedding_model=embeddings
        )
        
        if not docs:
            logger.info("No relevant documents found")
            state["retrieved_documents"] = []
            state["context_used"] = ""
            return state
        
        # Format retrieved documents
        retrieved_docs = []
        context_parts = []
        
        for i, doc in enumerate(docs):
            doc_dict = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": getattr(doc, 'score', 0.0)
            }
            retrieved_docs.append(doc_dict)
            context_parts.append(f"Document {i+1}: {doc.page_content}")
        
        state["retrieved_documents"] = retrieved_docs
        state["context_used"] = "\n\n".join(context_parts)
        
        logger.info(f"✅ Retrieved {len(retrieved_docs)} relevant documents for query: '{state['user_text'][:50]}...'")
        
    except Exception as e:
        error_msg = f"Document retrieval failed: {str(e)}"
        logger.error(error_msg)
        state["retrieved_documents"] = []
        state["context_used"] = ""
        # Don't set error_message as this is not critical - continue without RAG
    
    # Record processing time
    state["processing_time"]["retrieve"] = time.time() - start_time
    
    return state


def generate_node(state: ChatState) -> ChatState:
    """
    Node: Generate response using LLM with context and history
    
    Args:
        state: Current chat state
        
    Returns:
        Updated state with assistant_text
    """
    start_time = time.time()
    state["current_step"] = "generating"
    
    try:
        logger.info(f"Generating response for session {state['session_id']}")
        
        if not state["user_text"]:
            raise ValueError("No user text to respond to")
        
        # Initialize LLM if needed
        if not initialize_llm():
            raise RuntimeError("Failed to initialize LLM")
        
        llm = get_llm()
        
        # Build prompt with context and history
        prompt_builder = get_rag_prompt_builder()
        
        # Build conversation context
        conversation_context = ""
        if state["conversation_history"]:
            recent_history = state["conversation_history"][-3:]  # Last 3 turns
            history_parts = []
            for turn in recent_history:
                history_parts.append(f"User: {turn['user_text']}")
                history_parts.append(f"Assistant: {turn['assistant_text']}")
            conversation_context = "\n".join(history_parts)
        
        # Generate response
        if state["context_used"] and state["retrieved_documents"]:
            # Use RAG prompt with retrieved context
            logger.info(f"Using RAG context with {len(state['retrieved_documents'])} documents")
            
            # Build context from retrieved documents
            context_text = ""
            for i, doc in enumerate(state["retrieved_documents"]):
                context_text += f"Document {i+1}:\n{doc['content']}\n\n"
            
            # Create RAG-enhanced prompt
            system_prompt = """நீங்கள் ஒரு உதவிகரமான தமிழ் AI உதவியாளர். கொடுக்கப்பட்ட ஆவணங்களின் அடிப்படையில் பயனர்களுக்கு தமிழில் பதிலளிக்கவும். 

You are a helpful Tamil AI assistant. Answer user questions based on the provided documents. Respond in Tamil. Be accurate and cite the relevant information from the documents."""
            
            if conversation_context:
                prompt = f"""{system_prompt}

Context Documents:
{context_text}

Conversation History:
{conversation_context}

User: {state['user_text']}
Assistant: """
            else:
                prompt = f"""{system_prompt}

Context Documents:
{context_text}

User: {state['user_text']}
Assistant: """
        else:
            # Use general conversation prompt
            logger.info("No RAG context available, using general conversation prompt")
            system_prompt = """நீங்கள் ஒரு உதவிகரமான தமிழ் AI உதவியாளர். பயனர்களுக்கு தமிழில் பதிலளிக்கவும். 
            
You are a helpful Tamil AI assistant. Please respond to users in Tamil. Be conversational, helpful, and natural."""
            
            if conversation_context:
                prompt = f"{system_prompt}\n\nConversation History:\n{conversation_context}\n\nUser: {state['user_text']}\nAssistant:"
            else:
                prompt = f"{system_prompt}\n\nUser: {state['user_text']}\nAssistant:"
        
        # Generate response
        assistant_text = llm.generate(
            prompt,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE
        )
        
        if not assistant_text.strip():
            # Fallback response
            assistant_text = "மன்னிக்கவும், என்னால் இப்போது பதிலளிக்க முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்."
        
        state["assistant_text"] = assistant_text.strip()
        state["error_message"] = None
        
        logger.info(f"Response generated: {assistant_text[:50]}...")
        
    except Exception as e:
        error_msg = f"Response generation failed: {str(e)}"
        logger.error(error_msg)
        state["error_message"] = error_msg
        # Fallback response
        state["assistant_text"] = "மன்னிக்கவும், தொழில்நுட்ப சிக்கல் காரணமாக என்னால் பதிலளிக்க முடியவில்லை."
    
    # Record processing time
    state["processing_time"]["generate"] = time.time() - start_time
    
    return state


async def synthesize_node(state: ChatState) -> ChatState:
    """
    Node: Synthesize speech from assistant text using TTS
    
    Args:
        state: Current chat state
        
    Returns:
        Updated state with audio_output
    """
    start_time = time.time()
    state["current_step"] = "synthesizing"
    
    try:
        logger.info(f"Synthesizing speech for session {state['session_id']}")
        
        if not state["assistant_text"]:
            raise ValueError("No assistant text to synthesize")
        
        # Initialize TTS if needed
        if not initialize_tts():
            raise RuntimeError("Failed to initialize TTS engine")
        
        # Generate unique output filename
        output_filename = f"response_{state['session_id']}_{int(time.time())}.wav"

        # Synthesize speech (without saving to file)
        audio_data = synthesize_speech(
            state["assistant_text"],
            output_path=None  # Don't save locally, we'll upload to MinIO
        )

        if audio_data is not None:
            # Get user_id from session state
            user_id = state.get("user_id", "anonymous")
            
            # Upload TTS audio to MinIO
            minio_key = await upload_tts_audio_to_minio(
                audio_data=audio_data,
                session_id=state['session_id'],
                filename=output_filename,
                user_id=user_id
            )

            if minio_key:
                state["audio_output_path"] = minio_key  # Store MinIO key instead of local path
                state["audio_output"] = None  # Keep as None for now
                state["error_message"] = None
                logger.info(f"📁 TTS audio uploaded to MinIO: {minio_key}")
            else:
                state["error_message"] = "Failed to upload TTS audio to storage"
                state["audio_output_path"] = None
                logger.error(f"❌ Failed to upload TTS audio for session {state['session_id']}")
        else:
            state["error_message"] = "TTS synthesis failed"
            state["audio_output_path"] = None
            logger.error(f"❌ TTS synthesis failed for session {state['session_id']}")
        
    except Exception as e:
        error_msg = f"Speech synthesis failed: {str(e)}"
        logger.error(error_msg)
        state["error_message"] = error_msg
        state["audio_output"] = None
        state["audio_output_path"] = None
    
    # Record processing time
    state["processing_time"]["synthesize"] = time.time() - start_time
    
    return state


def history_node(state: ChatState) -> ChatState:
    """
    Node: Update conversation history with current turn
    
    Args:
        state: Current chat state
        
    Returns:
        Updated state with updated conversation_history
    """
    start_time = time.time()
    state["current_step"] = "updating_history"
    
    try:
        logger.info(f"Updating history for session {state['session_id']}")
        
        # Only add to history if we have both user and assistant text
        if state["user_text"] and state["assistant_text"]:
            turn_data = {
                "timestamp": datetime.now().isoformat(),
                "user_text": state["user_text"],
                "assistant_text": state["assistant_text"],
                "retrieved_documents": state["retrieved_documents"],
                "processing_time": state["processing_time"].copy(),
                "audio_input_path": state.get("audio_input_path"),
                "audio_output_path": state.get("audio_output_path")
            }
            
            # Add to conversation history
            state["conversation_history"].append(turn_data)
            
            # Trim history if it exceeds max turns
            if len(state["conversation_history"]) > state["max_history_turns"]:
                state["conversation_history"] = state["conversation_history"][-state["max_history_turns"]:]
            
            # Update turn counter
            state["total_turns"] += 1
            
            logger.info(f"Added turn to history. Total turns: {state['total_turns']}")
        
        state["current_step"] = "completed"
        
    except Exception as e:
        error_msg = f"History update failed: {str(e)}"
        logger.error(error_msg)
        # Don't fail the entire pipeline for history issues
    
    # Record processing time
    state["processing_time"]["history"] = time.time() - start_time
    
    return state


def should_use_rag(state: ChatState) -> str:
    """
    Conditional edge: Determine if RAG should be used
    
    Args:
        state: Current chat state
        
    Returns:
        Next node name
    """
    if state["rag_enabled"] and state["user_text"]:
        return "retrieve"
    else:
        return "generate"


def create_chat_graph() -> StateGraph:
    """
    Create the conversational chat graph
    
    Returns:
        Configured StateGraph
    """
    # Create graph
    graph = StateGraph(ChatState)
    
    # Add nodes
    graph.add_node("transcribe", transcribe_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("history", history_node)
    
    # Set entry point
    graph.set_entry_point("transcribe")
    
    # Add edges
    graph.add_conditional_edges(
        "transcribe",
        should_use_rag,
        {
            "retrieve": "retrieve",
            "generate": "generate"
        }
    )
    
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "synthesize")
    graph.add_edge("synthesize", "history")
    graph.add_edge("history", END)
    
    return graph


# Global chat graph instance
chat_graph = create_chat_graph()


async def process_conversation_turn_async(
    session_id: str,
    audio_input_path: Optional[str] = None,
    text_input: Optional[str] = None,
    language: str = "ta",
    db: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Process a complete conversation turn (async version with database persistence).
    
    Args:
        session_id: Session identifier
        audio_input_path: Path to user's audio input (optional if text_input provided)
        text_input: Direct text input (optional if audio_input_path provided)
        language: Language code
        db: Database session (optional)
        
    Returns:
        Processing results
    """
    try:
        # Get session manager
        session_manager = await get_or_create_session_manager()
        
        # Get database session if not provided
        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True
        
        try:
            # Use comprehensive session validation
            validation_result = await session_manager.validate_session_access(session_id, db=db_session)

            if not validation_result["valid"]:
                error_msg = validation_result.get("error", "Session validation failed")
                logger.error(f"Session validation failed for {session_id}: {error_msg}")

                # Map validation errors to specific error codes
                if "not found" in error_msg:
                    error_code = "SESSION_NOT_FOUND"
                elif "not active" in error_msg:
                    error_code = "SESSION_INACTIVE"
                elif "Invalid session ID" in error_msg:
                    error_code = "INVALID_SESSION_ID"
                else:
                    error_code = "SESSION_VALIDATION_ERROR"

                return {
                    "status": "error",
                    "error": error_msg,
                    "error_code": error_code,
                    "session_id": session_id,
                    "validation_details": validation_result
                }

            # Extract session data from validation result
            session_data = validation_result["session_data"]
            logger.debug(f"Session validation successful for: {session_id}")
            
            # Get conversation history
            history = await session_manager.get_conversation_history(session_id, db=db_session)
            
            # Convert to ChatState format
            state = _convert_db_session_to_chat_state(session_data, history)
            
            # Validate input parameters
            if not audio_input_path and not text_input:
                logger.error(f"No input provided for session {session_id}")
                return {
                    "status": "error",
                    "error": "Either audio_input_path or text_input must be provided",
                    "error_code": "MISSING_INPUT",
                    "session_id": session_id
                }

            # Validate session_id format
            if not session_id or not isinstance(session_id, str):
                logger.error(f"Invalid session_id format: {session_id}")
                return {
                    "status": "error",
                    "error": "Invalid session_id format",
                    "error_code": "INVALID_SESSION_ID",
                    "session_id": session_id
                }

            logger.debug(f"Input validation successful for session: {session_id}")
            
            # Set up current turn
            state["audio_input_path"] = audio_input_path
            state["language"] = language
            state["user_text"] = text_input or ""
            state["assistant_text"] = ""
            state["audio_output_path"] = None
            state["error_message"] = None
            state["processing_time"] = {}
            
            # Process conversation turn
            if text_input:
                # Skip transcription, go directly to RAG/generation
                logger.info(f"Processing text input for session {state['session_id']}")
                
                # Retrieve (if RAG enabled)
                result = retrieve_node(state)
                
                # Generate
                result = generate_node(result)
                
                # Synthesize
                result = synthesize_node(result)
                
                # Update history (in-memory)
                result = history_node(result)
            else:
                # Process through full graph (including transcription)
                compiled_graph = chat_graph.compile()
                result = compiled_graph.invoke(state)
            
            # Persist conversation turn to database
            if result["user_text"] and result["assistant_text"]:
                # Extract retrieved chunk IDs
                retrieved_chunks = [
                    doc.get("metadata", {}).get("chunk_id", f"chunk_{i}")
                    for i, doc in enumerate(result["retrieved_documents"])
                ]
                
                turn_id = await session_manager.add_conversation_turn(
                    session_id=session_id,
                    user_text=result["user_text"],
                    assistant_text=result["assistant_text"],
                    audio_input_key=audio_input_path,
                    audio_output_key=result.get("audio_output_path"),
                    retrieved_chunks=retrieved_chunks,
                    processing_time=result["processing_time"],
                    db=db_session
                )
                
                if turn_id:
                    logger.info(f"Persisted conversation turn {turn_id} to database")
                else:
                    logger.warning(f"Failed to persist conversation turn to database")
            
            # Return results
            return {
                "status": "completed",
                "session_id": session_id,
                "user_text": result["user_text"],
                "assistant_text": result["assistant_text"],
                "audio_output_path": result.get("audio_output_path"),
                "processing_time": result["processing_time"],
                "total_time": sum(result["processing_time"].values()),
                "retrieved_documents": len(result["retrieved_documents"]),
                "error": result.get("error_message")
            }
            
        finally:
            if should_close_db:
                # Note: Do not close session manually - async context manager handles it
                pass

    except Exception as e:
        error_msg = f"Conversation processing failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Include more detailed error information for debugging
        error_details = {
            "exception_type": type(e).__name__,
            "exception_message": str(e),
        }

        return {
            "status": "error",
            "error": error_msg,
            "error_code": "PROCESSING_FAILED",
            "error_details": error_details,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }


def process_conversation_turn(
    session_id: str,
    audio_input_path: Optional[str] = None,
    text_input: Optional[str] = None,
    language: str = "ta"
) -> Dict[str, Any]:
    """
    Process a complete conversation turn (sync wrapper for backward compatibility).
    
    Args:
        session_id: Session identifier
        audio_input_path: Path to user's audio input (optional if text_input provided)
        text_input: Direct text input (optional if audio_input_path provided)
        language: Language code
        
    Returns:
        Processing results
    """
    # Run async function in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            process_conversation_turn_async(session_id, audio_input_path, text_input, language)
        )
    finally:
        loop.close()


def create_session(
    user_id: Optional[str] = None,
    language: str = "ta",
    rag_enabled: bool = True
) -> str:
    """
    Create a new conversation session (sync wrapper).
    
    Args:
        user_id: Optional user identifier
        language: Conversation language
        rag_enabled: Enable RAG retrieval
        
    Returns:
        Session ID
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def _create():
            manager = await get_or_create_session_manager()
            return await manager.create_session(user_id, language, rag_enabled)
        return loop.run_until_complete(_create())
    finally:
        loop.close()


def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session information (sync wrapper).
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session info or None
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def _get():
            manager = await get_or_create_session_manager()
            return await manager.get_session(session_id)
        return loop.run_until_complete(_get())
    finally:
        loop.close()


def delete_session(session_id: str) -> bool:
    """
    Delete a conversation session (sync wrapper).
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if deleted
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def _delete():
            manager = await get_or_create_session_manager()
            return await manager.delete_session(session_id)
        return loop.run_until_complete(_delete())
    finally:
        loop.close()


def get_conversation_history(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get conversation history for a session (sync wrapper).
    
    Args:
        session_id: Session identifier
        
    Returns:
        Conversation history or None
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def _get_history():
            manager = await get_or_create_session_manager()
            return await manager.get_conversation_history(session_id)
        return loop.run_until_complete(_get_history())
    finally:
        loop.close()


def list_active_sessions() -> Dict[str, Dict[str, Any]]:
    """
    Get all active sessions with their info (sync wrapper).
    
    Returns:
        Dictionary of session_id -> session_info
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def _list():
            manager = await get_or_create_session_manager()
            # Get all active sessions from database
            db_session = await anext(get_db())
            try:
                sessions = await manager.list_user_sessions(
                    user_id=None,  # Get all sessions
                    status_filter=None,
                    limit=100,
                    db=db_session
                )
                result = {}
                for session in sessions:
                    result[session["session_id"]] = session
                return result
            finally:
                await db_session.close()
        return loop.run_until_complete(_list())
    finally:
        loop.close()


def get_session_stats() -> Dict[str, Any]:
    """
    Get global session statistics (sync wrapper).
    
    Returns:
        Session statistics with format expected by API
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def _get_stats():
            manager = await get_or_create_session_manager()
            # Get stats from database using async generator
            async for db_session in get_db():
                try:
                    from sqlalchemy import func, select
                    from backend.database.models import ConversationSession, ConversationTurn, SessionStatus
                    
                    # Count total sessions
                    total_result = await db_session.execute(
                        select(func.count(ConversationSession.id))
                    )
                    total_sessions = total_result.scalar() or 0
                    
                    # Count active sessions
                    active_result = await db_session.execute(
                        select(func.count(ConversationSession.id))
                        .where(ConversationSession.status == SessionStatus.ACTIVE)
                    )
                    active_sessions = active_result.scalar() or 0
                    
                    # Count total turns
                    turns_result = await db_session.execute(
                        select(func.count(ConversationTurn.id))
                    )
                    total_turns = turns_result.scalar() or 0
                    
                    return {
                        "total_sessions": total_sessions,
                        "active_sessions": active_sessions,
                        "total_turns": total_turns,
                        "average_session_duration": 0.0,  # TODO: Calculate from session data
                        "average_turn_time": 0.0  # TODO: Calculate from turn processing_time
                    }
                except Exception as e:
                    logger.error(f"Failed to get stats: {e}")
                    return {
                        "total_sessions": 0,
                        "active_sessions": 0,
                        "total_turns": 0,
                        "average_session_duration": 0.0,
                        "average_turn_time": 0.0
                    }
        return loop.run_until_complete(_get_stats())
    finally:
        loop.close()


if __name__ == "__main__":
    # Test the chat graph
    print("="*70)
    print("🧪 Testing Conversational Chat Graph")
    print("="*70)
    
    # Create test session
    session_id = create_session(language="ta", rag_enabled=False)
    print(f"Created test session: {session_id}")
    
    # Test with mock audio (would need actual audio file)
    # For now, just test the graph structure
    print("\nGraph structure:")
    print(f"Nodes: {list(chat_graph.nodes.keys())}")
    print(f"Edges: {chat_graph.edges}")
    
    print("\nSession info:")
    info = get_session_info(session_id)
    if info:
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    print("\nSession stats:")
    stats = get_session_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Clean up
    delete_session(session_id)
    print(f"\nDeleted test session: {session_id}")
    
    print("\n" + "="*70)
    print("✅ Chat graph test complete!")
    print("="*70)
