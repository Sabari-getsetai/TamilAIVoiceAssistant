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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from backend.settings import settings
from backend.speech import (
    initialize_stt, initialize_tts,
    get_stt_engine, get_tts_engine,
    transcribe_audio, synthesize_speech
)
from backend.models import get_llm, initialize_llm
from backend.rag import (
    get_embedding_model, VectorStore,
    get_rag_prompt_builder
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class SessionManager:
    """
    Manages chat sessions with automatic cleanup and persistence
    
    Features:
    - Session creation and retrieval
    - Automatic session cleanup
    - Concurrent session support
    - Session analytics
    """
    
    def __init__(self):
        self.sessions: Dict[str, ChatState] = {}
        self.session_timeout = timedelta(minutes=settings.CHAT_SESSION_TIMEOUT_MINUTES)
        
    def create_session(
        self,
        user_id: Optional[str] = None,
        language: str = "ta",
        rag_enabled: bool = True
    ) -> str:
        """
        Create a new chat session
        
        Args:
            user_id: Optional user identifier
            language: Conversation language (ta, en)
            rag_enabled: Enable RAG document retrieval
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        initial_state: ChatState = {
            # Session management
            "session_id": session_id,
            "user_id": user_id,
            "created_at": now,
            "last_activity": now,
            
            # Current turn
            "audio_input": None,
            "audio_input_path": None,
            "user_text": "",
            "assistant_text": "",
            "audio_output": None,
            "audio_output_path": None,
            
            # Conversation history
            "conversation_history": [],
            
            # RAG context
            "retrieved_documents": [],
            "context_used": "",
            "rag_enabled": rag_enabled,
            
            # Processing status
            "current_step": "initialized",
            "error_message": None,
            "processing_time": {},
            
            # Configuration
            "language": language,
            "max_history_turns": settings.CHAT_MAX_HISTORY_TURNS,
            
            # Metadata
            "total_turns": 0,
            "session_duration": 0.0
        }
        
        self.sessions[session_id] = initial_state
        logger.info(f"Created new session: {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatState]:
        """
        Retrieve session state
        
        Args:
            session_id: Session identifier
            
        Returns:
            ChatState or None if not found
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Check if session has expired
            if datetime.now() - session["last_activity"] > self.session_timeout:
                logger.info(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None
            
            return session
        
        return None
    
    def update_session(self, session_id: str, state: ChatState) -> bool:
        """
        Update session state
        
        Args:
            session_id: Session identifier
            state: Updated state
            
        Returns:
            True if successful
        """
        if session_id in self.sessions:
            state["last_activity"] = datetime.now()
            state["session_duration"] = (
                state["last_activity"] - state["created_at"]
            ).total_seconds()
            
            self.sessions[session_id] = state
            return True
        
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session["last_activity"] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def list_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs
        
        Returns:
            List of session IDs
        """
        self.cleanup_expired_sessions()
        return list(self.sessions.keys())
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Session statistics
        """
        self.cleanup_expired_sessions()
        
        if not self.sessions:
            return {
                "total_sessions": 0,
                "average_duration": 0.0,
                "total_turns": 0
            }
        
        total_duration = sum(s["session_duration"] for s in self.sessions.values())
        total_turns = sum(s["total_turns"] for s in self.sessions.values())
        
        return {
            "total_sessions": len(self.sessions),
            "average_duration": total_duration / len(self.sessions),
            "total_turns": total_turns,
            "average_turns_per_session": total_turns / len(self.sessions) if self.sessions else 0
        }


# Global session manager
session_manager = SessionManager()


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


def synthesize_node(state: ChatState) -> ChatState:
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
        
        # Generate unique output path
        output_filename = f"response_{state['session_id']}_{int(time.time())}.wav"
        output_path = settings.AUDIO_OUT_DIR / output_filename
        
        # Synthesize speech
        audio_data = synthesize_speech(
            state["assistant_text"],
            output_path=str(output_path)
        )
        
        if audio_data is not None:
            state["audio_output_path"] = str(output_path)
            # Could also store audio_data as bytes if needed
            state["audio_output"] = None  # For now, just use file path
            state["error_message"] = None
            
            logger.info(f"Speech synthesis successful: {output_path}")
        else:
            raise RuntimeError("TTS synthesis returned None")
        
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


def process_conversation_turn(
    session_id: str,
    audio_input_path: Optional[str] = None,
    text_input: Optional[str] = None,
    language: str = "ta"
) -> Dict[str, Any]:
    """
    Process a complete conversation turn
    
    Args:
        session_id: Session identifier
        audio_input_path: Path to user's audio input (optional if text_input provided)
        text_input: Direct text input (optional if audio_input_path provided)
        language: Language code
        
    Returns:
        Processing results
    """
    try:
        # Get or create session
        state = session_manager.get_session(session_id)
        if not state:
            logger.error(f"Session not found: {session_id}")
            return {
                "status": "error",
                "error": "Session not found",
                "session_id": session_id
            }
        
        # Validate input
        if not audio_input_path and not text_input:
            return {
                "status": "error",
                "error": "Either audio_input_path or text_input must be provided",
                "session_id": session_id
            }
        
        # Set up current turn
        state["audio_input_path"] = audio_input_path
        state["language"] = language
        state["user_text"] = text_input or ""  # Use text_input directly if provided
        state["assistant_text"] = ""
        state["audio_output_path"] = None
        state["error_message"] = None
        state["processing_time"] = {}
        
        # If text input is provided, skip transcription
        if text_input:
            # Skip transcription, go directly to RAG/generation
            logger.info(f"Processing text input for session {state['session_id']}")
            
            # Process retrieve -> generate -> synthesize -> history
            start_time = time.time()
            
            # Retrieve (if RAG enabled)
            result = retrieve_node(state)
            
            # Generate
            result = generate_node(result)
            
            # Synthesize
            result = synthesize_node(result)
            
            # Update history
            result = history_node(result)
            
        else:
            # Process through full graph (including transcription)
            compiled_graph = chat_graph.compile()
            result = compiled_graph.invoke(state)
        
        # Update session
        session_manager.update_session(session_id, result)
        
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
        
    except Exception as e:
        error_msg = f"Conversation processing failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "session_id": session_id
        }


def create_session(
    user_id: Optional[str] = None,
    language: str = "ta",
    rag_enabled: bool = True
) -> str:
    """
    Create a new conversation session
    
    Args:
        user_id: Optional user identifier
        language: Conversation language
        rag_enabled: Enable RAG retrieval
        
    Returns:
        Session ID
    """
    return session_manager.create_session(
        user_id=user_id,
        language=language,
        rag_enabled=rag_enabled
    )


def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session information
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session info or None
    """
    state = session_manager.get_session(session_id)
    if not state:
        return None
    
    return {
        "session_id": state["session_id"],
        "user_id": state["user_id"],
        "created_at": state["created_at"].isoformat(),
        "last_activity": state["last_activity"].isoformat(),
        "total_turns": state["total_turns"],
        "session_duration": state["session_duration"],
        "language": state["language"],
        "rag_enabled": state["rag_enabled"],
        "current_step": state["current_step"]
    }


def delete_session(session_id: str) -> bool:
    """
    Delete a conversation session
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if deleted
    """
    return session_manager.delete_session(session_id)


def get_conversation_history(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get conversation history for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Conversation history or None
    """
    state = session_manager.get_session(session_id)
    if not state:
        return None
    
    return state["conversation_history"]


def list_active_sessions() -> Dict[str, Dict[str, Any]]:
    """
    Get all active sessions with their info
    
    Returns:
        Dictionary of session_id -> session_info
    """
    session_manager.cleanup_expired_sessions()
    result = {}
    for session_id in session_manager.sessions.keys():
        info = get_session_info(session_id)
        if info:
            result[session_id] = info
    return result


def get_session_stats() -> Dict[str, Any]:
    """
    Get global session statistics
    
    Returns:
        Session statistics with format expected by API
    """
    session_manager.cleanup_expired_sessions()
    
    if not session_manager.sessions:
        return {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_turns": 0,
            "average_session_duration": 0.0,
            "average_turn_time": 0.0
        }
    
    total_turns = sum(s["total_turns"] for s in session_manager.sessions.values())
    total_duration = sum(s["session_duration"] for s in session_manager.sessions.values())
    
    # Calculate average turn time from processing times
    all_turn_times = []
    for session in session_manager.sessions.values():
        for turn in session["conversation_history"]:
            turn_time = sum(turn.get("processing_time", {}).values())
            if turn_time > 0:
                all_turn_times.append(turn_time)
    
    avg_turn_time = sum(all_turn_times) / len(all_turn_times) if all_turn_times else 0.0
    
    return {
        "total_sessions": len(session_manager.sessions),
        "active_sessions": len(session_manager.sessions),
        "total_turns": total_turns,
        "average_session_duration": total_duration / len(session_manager.sessions),
        "average_turn_time": avg_turn_time
    }


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
