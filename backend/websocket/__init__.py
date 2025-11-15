"""
WebSocket Package - Modular Real-Time Communication

This package contains modular WebSocket components for real-time voice conversation,
replacing the monolithic websocket.py with clean, testable, and maintainable components.

Components:
- websocket_router: Main WebSocket endpoints and routing
- message_handlers: Specialized handlers for different message types
- audio_processor: Audio processing and pipeline integration
- ConnectionManager: Connection lifecycle management (legacy component)
"""

from .websocket_router import router as websocket_router
from .message_handlers import (
    message_handler_registry,
    BaseMessageHandler,
    AudioChunkHandler,
    StartSpeakingHandler,
    StopSpeakingHandler,
    InterruptHandler,
    ConfigUpdateHandler,
    WelcomeMessageHandler,
    MessageHandlerRegistry
)
from .audio_processor import AudioProcessor

# Legacy import for backward compatibility
try:
    from .ConnectionManager import manager as connection_manager
except ImportError:
    connection_manager = None

__all__ = [
    # Main router
    "websocket_router",

    # Message handling
    "message_handler_registry",
    "BaseMessageHandler",
    "AudioChunkHandler",
    "StartSpeakingHandler",
    "StopSpeakingHandler",
    "InterruptHandler",
    "ConfigUpdateHandler",
    "WelcomeMessageHandler",
    "MessageHandlerRegistry",

    # Audio processing
    "AudioProcessor",

    # Legacy components
    "connection_manager"
]