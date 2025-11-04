"""
API Endpoints Package

Contains FastAPI routers for:
- Admin endpoints (admin.py)
- Chat endpoints (chat.py) - planned
"""

from .admin import router as admin_router
from .chat import router as chat_router
from .speech import router as speech_router
from .simple_chat import router as simple_chat_router
from .websocket import router as websocket_router

__all__ = ["admin_router", "chat_router", "speech_router", "simple_chat_router", "websocket_router"]
