"""Modular WebSocket Router

This module provides a clean, modular WebSocket implementation that replaces
the monolithic websocket.py with properly separated concerns.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.websocket.message_handlers import message_handler_registry
from backend.websocket.audio_processor import AudioProcessor
from backend.websocket.ConnectionManager import manager as connection_manager


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])

# Initialize components
audio_processor = AudioProcessor()


@router.websocket("/voice/{session_id}")
async def websocket_voice_endpoint(websocket: WebSocket, session_id: str):
    """
    Modular WebSocket endpoint for real-time voice conversation

    Message Types:
    - audio_chunk: Raw audio data for processing
    - start_speaking: User started speaking
    - stop_speaking: User stopped speaking
    - interrupt: Interrupt assistant speech
    - config_update: Update session configuration
    """
    logger.info(f"WebSocket connection attempt for session {session_id}")

    try:
        # Establish connection through connection manager
        await connection_manager.connect(websocket, session_id)

        # Validate connection was successful
        if session_id not in connection_manager.session_data:
            logger.error(f"Session {session_id} not found in manager after connection attempt")
            await websocket.close(code=1003, reason="Session initialization failed")
            return

        session = connection_manager.session_data[session_id]
        logger.info(f"WebSocket connection established for session {session_id}")

    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection for session {session_id}: {str(e)}")
        try:
            await websocket.close(code=1003, reason="Connection failed")
        except:
            pass
        return

    try:
        # Send initial connection confirmation
        await connection_manager.send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "server_capabilities": {
                "audio_processing": True,
                "real_time_response": True,
                "rag_support": True,
                "multi_language": True
            }
        })

        # Send welcome message
        await message_handler_registry.send_welcome_message(session_id, session)

        # Main message processing loop
        await _handle_message_loop(websocket, session_id, session)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
    finally:
        # Cleanup
        await _cleanup_session(session_id)


async def _handle_message_loop(websocket: WebSocket, session_id: str, session: Dict[str, Any]) -> None:
    """Handle the main WebSocket message processing loop"""
    while True:
        try:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Validate message format
            if not isinstance(message, dict) or "type" not in message:
                await connection_manager.send_error(session_id, "Invalid message format")
                continue

            message_type = message.get("type")
            logger.debug(f"Received message type '{message_type}' for session {session_id}")

            # Handle message through registry
            success = await message_handler_registry.handle_message(
                message_type=message_type,
                session_id=session_id,
                message=message,
                session=session,
                manager=connection_manager
            )

            if not success:
                logger.warning(f"Message handling failed for type '{message_type}' in session {session_id}")

        except WebSocketDisconnect:
            logger.info(f"Client disconnected from session {session_id}")
            break
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON received for session {session_id}: {str(e)}")
            await connection_manager.send_error(session_id, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {str(e)}")
            await connection_manager.send_error(session_id, f"Message processing error: {str(e)}")


async def _cleanup_session(session_id: str) -> None:
    """Clean up session resources"""
    try:
        # Disconnect through connection manager
        await connection_manager.disconnect(session_id)
        logger.info(f"Session cleanup completed for {session_id}")
    except Exception as e:
        logger.error(f"Error during session cleanup for {session_id}: {str(e)}")


@router.get("/health")
async def websocket_health():
    """WebSocket health check endpoint"""
    try:
        # Check connection manager health
        manager_health = connection_manager.get_connection_stats()

        # Check message handler registry
        handler_info = message_handler_registry.get_handler_info()

        # Check audio processor
        processor_status = audio_processor.get_processor_status()

        # Overall health determination
        is_healthy = (
            manager_health.get("active_connections", 0) >= 0 and  # Manager is responsive
            len(handler_info.get("registered_handlers", [])) > 0 and  # Handlers loaded
            processor_status.get("audio_service_loaded", False)  # Audio service available
        )

        health_status = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "connection_manager": {
                    "status": "healthy",
                    "active_connections": manager_health.get("active_connections", 0),
                    "total_sessions": manager_health.get("total_sessions", 0)
                },
                "message_handlers": {
                    "status": "healthy" if len(handler_info.get("registered_handlers", [])) > 0 else "unhealthy",
                    "registered_handlers": handler_info.get("registered_handlers", []),
                    "handler_count": len(handler_info.get("registered_handlers", []))
                },
                "audio_processor": {
                    "status": "healthy" if processor_status.get("audio_service_loaded", False) else "unhealthy",
                    "sample_rate": processor_status.get("sample_rate"),
                    "max_buffer_duration": processor_status.get("max_buffer_duration")
                }
            }
        }

        status_code = 200 if is_healthy else 503
        return JSONResponse(content=health_status, status_code=status_code)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )


@router.get("/sessions")
async def list_active_sessions():
    """List all active WebSocket sessions"""
    try:
        stats = connection_manager.get_connection_stats()
        session_details = {}

        for session_id in connection_manager.session_data:
            session = connection_manager.session_data[session_id]
            session_details[session_id] = {
                "connected_at": session.get("connected_at"),
                "last_activity": session.get("last_activity"),
                "is_speaking": session.get("is_speaking", False),
                "is_processing": session.get("is_processing", False),
                "config": session.get("config", {}),
                "speech_buffer_size": len(session.get("speech_buffer", []))
            }

        return {
            "active_sessions": stats.get("active_connections", 0),
            "total_sessions": stats.get("total_sessions", 0),
            "session_details": session_details,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a specific session"""
    try:
        if session_id not in connection_manager.session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        session = connection_manager.session_data[session_id]

        return {
            "session_id": session_id,
            "connected_at": session.get("connected_at"),
            "last_activity": session.get("last_activity"),
            "is_speaking": session.get("is_speaking", False),
            "is_processing": session.get("is_processing", False),
            "speech_buffer_size": len(session.get("speech_buffer", [])),
            "config": session.get("config", {}),
            "websocket_connected": session_id in connection_manager.connections,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info for {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/disconnect")
async def disconnect_session(session_id: str):
    """Forcefully disconnect a WebSocket session"""
    try:
        if session_id not in connection_manager.session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Disconnect the session
        await connection_manager.disconnect(session_id)

        return {
            "message": f"Session {session_id} disconnected successfully",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_websocket_config():
    """Get current WebSocket configuration"""
    try:
        handler_info = message_handler_registry.get_handler_info()
        processor_status = audio_processor.get_processor_status()
        manager_stats = connection_manager.get_connection_stats()

        return {
            "websocket_config": {
                "max_connections": getattr(connection_manager, 'max_connections', 100),
                "connection_timeout": getattr(connection_manager, 'connection_timeout', 300)
            },
            "message_handlers": handler_info,
            "audio_processor": processor_status,
            "connection_manager": manager_stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting WebSocket config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/audio_processor")
async def update_audio_processor_config(
    sample_rate: int = None,
    chunk_size: int = None,
    max_buffer_duration: float = None,
    silence_threshold: float = None,
    min_speech_duration: float = None
):
    """Update audio processor configuration"""
    try:
        audio_processor.configure_processor(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            max_buffer_duration=max_buffer_duration,
            silence_threshold=silence_threshold,
            min_speech_duration=min_speech_duration
        )

        return {
            "message": "Audio processor configuration updated",
            "new_config": audio_processor.get_processor_status(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error updating audio processor config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))