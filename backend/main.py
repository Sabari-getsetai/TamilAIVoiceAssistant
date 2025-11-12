"""
Tamil AI Voice Assistant - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys
from pathlib import Path
import asyncio

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from settings import settings
from api import auth_router, admin_v2_router, chat_router, speech_router, simple_chat_router, websocket_router, organization_router

# Infrastructure imports
from database.connection import init_db_with_retry, check_db_health, get_db_info
from storage.minio_client import init_buckets_with_retry, check_minio_health, get_minio_info
from cache.redis_client import init_redis_with_retry, check_redis_health, get_redis_info
from infrastructure.health import get_health_checker, monitor_services

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
app.include_router(auth_router)
app.include_router(admin_v2_router)  # Database-integrated admin endpoints
app.include_router(chat_router)
app.include_router(speech_router)
app.include_router(simple_chat_router)
app.include_router(websocket_router)
app.include_router(organization_router)


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
    """Enhanced health check endpoint with detailed infrastructure status"""
    try:
        health_checker = get_health_checker()
        overall_health = await health_checker.get_overall_health()
        
        # Add additional service info
        overall_health["services"]["api"] = {
            "status": "healthy",
            "connection_state": "connected",
            "last_check": datetime.now().isoformat(),
            "metadata": {"version": "0.1.0"}
        }
        
        # Add models and vector store status (existing logic)
        overall_health["services"]["models"] = {
            "status": "unknown",
            "connection_state": "unknown", 
            "last_check": datetime.now().isoformat(),
            "metadata": {"loaded": False}
        }
        
        overall_health["services"]["vector_store"] = {
            "status": "unknown",
            "connection_state": "unknown",
            "last_check": datetime.now().isoformat(), 
            "metadata": {"initialized": False}
        }
        
        return overall_health
        
    except Exception as e:
        # Fallback to simple health check if enhanced monitoring fails
        return {
            "overall_status": "degraded",
            "services": {
                "api": {"status": "healthy", "error": None},
                "database": {"status": "unknown", "error": "Health monitoring unavailable"},
                "minio": {"status": "unknown", "error": "Health monitoring unavailable"},
                "redis": {"status": "unknown", "error": "Health monitoring unavailable"},
            },
            "summary": {
                "total_services": 4,
                "healthy_services": 1,
                "unhealthy_services": 0,
                "failed_services": 0,
            },
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service information"""
    try:
        # Get detailed info from each service
        db_info = await get_db_info()
        minio_info = await get_minio_info()
        redis_info = await get_redis_info()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_info,
                "minio": minio_info,
                "redis": redis_info,
            }
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "services": {}
        }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Tamil AI Voice Assistant starting...")
    print(f"📁 Data directory: {settings.DATA_ROOT}")
    print(f"🤖 Models directory: {settings.MODELS_ROOT}")
    print(f"🌐 API running on http://{settings.API_HOST}:{settings.API_PORT}")

    # Initialize infrastructure services
    print("\n🔧 Initializing infrastructure services...")

    # Track initialization status
    services_status = {"database": False, "minio": False, "redis": False}
    
    # Initialize database with retry
    try:
        print("📊 Initializing PostgreSQL database with retry logic...")
        await init_db_with_retry(max_retries=5, initial_delay=1.0)
        services_status["database"] = True
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("⚠️  Continuing without database (degraded functionality)")

    # Initialize MinIO with retry
    try:
        print("📦 Initializing MinIO buckets with retry logic...")
        await init_buckets_with_retry(max_retries=5, initial_delay=1.0)
        services_status["minio"] = True
        print("✅ MinIO buckets initialized successfully")
    except Exception as e:
        print(f"❌ MinIO initialization failed: {e}")
        print("⚠️  Continuing without MinIO (degraded functionality)")

    # Initialize Redis with retry
    try:
        print("🔄 Initializing Redis cache with retry logic...")
        await init_redis_with_retry(max_retries=5, initial_delay=1.0)
        services_status["redis"] = True
        print("✅ Redis cache initialized successfully")
    except Exception as e:
        print(f"❌ Redis initialization failed: {e}")
        print("⚠️  Continuing without Redis (degraded functionality)")
    
    # Set up health monitoring for initialized services
    try:
        health_checker = get_health_checker()
        if services_status["database"]:
            health_checker.add_service("database", check_db_health, check_interval=30.0)
        if services_status["minio"]:
            health_checker.add_service("minio", check_minio_health, check_interval=30.0)
        if services_status["redis"]:
            health_checker.add_service("redis", check_redis_health, check_interval=30.0)
        print("✅ Health monitoring configured")
    except Exception as e:
        print(f"⚠️  Health monitoring setup failed: {e}")
    
    # Print summary
    initialized_count = sum(services_status.values())
    total_count = len(services_status)
    print(f"\n📊 Services initialized: {initialized_count}/{total_count}")
    for service, status in services_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {'ready' if status else 'unavailable'}")

    print("\n✅ Tamil AI Voice Assistant started successfully!")


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
