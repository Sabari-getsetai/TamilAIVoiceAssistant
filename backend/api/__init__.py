"""
API Endpoints Package

Contains FastAPI routers for:
- Auth endpoints (auth.py)
- Admin endpoints (admin.py)
- Chat endpoints (chat.py)
- Speech endpoints (speech.py)
- WebSocket endpoints (websocket.py)
"""

from .auth import router as auth_router
from .admin import router as admin_router  # Legacy admin endpoints
from .admin_v2 import router as admin_v2_router  # Database-integrated admin endpoints
from .chat import router as chat_router
from .speech import router as speech_router
from .simple_chat import router as simple_chat_router
from .websocket import router as websocket_router
from .organization import router as organization_router

__all__ = [
    "auth_router",
    "admin_router",
    "admin_v2_router",
    "chat_router",
    "speech_router",
    "simple_chat_router",
    "websocket_router",
    "organization_router"
]
