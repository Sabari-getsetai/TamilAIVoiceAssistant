"""
Simple Chat API Endpoint - Proxy route for frontend compatibility

Provides simplified chat endpoint that proxies to the session-based chat API:
- /api/chat - Simple text chat without explicit session management
"""
import sys
from pathlib import Path
from typing import Optional


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.graphs.chat_graph import (
    create_session,
    process_conversation_turn,
    get_session_info,
)

# Create router
router = APIRouter(prefix="/api", tags=["simple-chat"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Simple chat request"""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Simple chat response"""
    response: str
    conversation_id: str
    sources: Optional[list] = None


# ============================================================================
# Global session storage for simple API
# ============================================================================

# Simple in-memory storage for conversation_id to session_id mapping
_conversation_sessions = {}


# ============================================================================
# Chat API Endpoint
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def simple_chat(request: ChatRequest) -> ChatResponse:
    """
    Simple chat endpoint that handles session management automatically
    
    Args:
        request: Chat request with message and optional conversation_id
        
    Returns:
        Chat response with AI-generated text
    """
    try:
        session_id = None
        conversation_id = request.conversation_id
        
        # Handle session management
        if conversation_id and conversation_id in _conversation_sessions:
            # Use existing session
            session_id = _conversation_sessions[conversation_id]
            
            # Verify session still exists
            session_info = get_session_info(session_id)
            if not session_info:
                # Session expired, create new one
                session_id = None
        
        if not session_id:
            # Create new session
            session_id = create_session(
                user_id=None,
                language="ta",
                rag_enabled=True,
            )
            
            # Generate conversation_id if not provided
            if not conversation_id:
                import uuid
                conversation_id = str(uuid.uuid4())
            
            # Store mapping
            _conversation_sessions[conversation_id] = session_id

        # Process the conversation turn
        result = process_conversation_turn(
            session_id=session_id,
            text_input=request.message,
            language="ta",
        )
        
        if result["status"] != "completed":
            error_msg = result.get("error", "Unknown error occurred")
            raise HTTPException(status_code=500, detail=f"Chat processing failed: {error_msg}")

        # Extract sources if available (from RAG)
        sources = None
        if "context_documents" in result:
            sources = [
                {
                    "content": doc.get("content", ""),
                    "metadata": {
                        "source": doc.get("metadata", {}).get("source", "unknown"),
                        "page": doc.get("metadata", {}).get("page"),
                    }
                }
                for doc in result["context_documents"]
            ]

        return ChatResponse(
            response=result.get("assistant_text", ""),
            conversation_id=conversation_id,
            sources=sources,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {e}")


@router.delete("/chat/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and its associated session
    
    Args:
        conversation_id: Conversation identifier
        
    Returns:
        Deletion confirmation
    """
    try:
        if conversation_id in _conversation_sessions:
            session_id = _conversation_sessions[conversation_id]
            
            # Delete session (import here to avoid circular imports)
            from backend.graphs.chat_graph import delete_session
            delete_session(session_id)
            
            # Remove from mapping
            del _conversation_sessions[conversation_id]
            
            return {"success": True, "message": f"Conversation {conversation_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {e}")
