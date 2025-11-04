"""
Tamil AI Voice Assistant - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from settings import settings
from api import admin_router, chat_router, speech_router, simple_chat_router, websocket_router

# Create FastAPI application
app = FastAPI(
    title="Tamil AI Voice Assistant",
    description="Offline Tamil conversational AI assistant with RAG capabilities",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(speech_router)
app.include_router(simple_chat_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Tamil AI Voice Assistant",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "models": "not loaded",  # Will be updated when models are loaded
            "vector_store": "not initialized",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Tamil AI Voice Assistant starting...")
    print(f"📁 Data directory: {settings.DATA_ROOT}")
    print(f"🤖 Models directory: {settings.MODELS_ROOT}")
    print(f"🌐 API running on http://{settings.API_HOST}:{settings.API_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Tamil AI Voice Assistant shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
