"""
API Endpoints Package

Contains FastAPI routers for:
- Auth endpoints (auth.py)
- Admin endpoints (admin.py)
- Chat endpoints (chat.py)
- Speech endpoints (speech.py)
- WebSocket endpoints (websocket.py)
"""

from .routes.auth import router as auth_router
from .routes.admin_v2 import router as admin_v2_router  # Database-integrated admin endpoints
from .routes.audit import router as audit_router  # Audit trail endpoints
from .routes.chat import router as chat_router
from .routes.speech import router as speech_router
from .routes.audio import router as audio_router  # Audio file access endpoints
from .tests.simple_chat import router as simple_chat_router
from .websocket import router as websocket_router
from .routes.organization import router as organization_router

__all__ = [
    "auth_router",
    "admin_v2_router",
    "audit_router",
    "chat_router",
    "speech_router",
    "audio_router",
    "simple_chat_router",
    "websocket_router",
    "organization_router"
]
