# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Tamil AI Voice Assistant - a production-ready, database-integrated conversational AI system that enables live phone call-like conversations in Tamil. It combines real-time voice processing, document intelligence, and multi-user management in a fully offline-capable system.

**Core System Architecture:**
- **Database-first design**: PostgreSQL 16 + pgVector for vector similarity search and session persistence
- **Microservice-ready infrastructure**: FastAPI backend with MinIO object storage + Redis caching
- **Real-time voice conversations**: WebSocket-based continuous dialogue with STT → RAG → LLM → TTS pipeline
- **Document intelligence**: RAG-powered QA over uploaded documents with 384-dimensional multilingual embeddings
- **Multi-tenant ready**: User authentication, organizations, and role-based access control
- **Tamil-first language support**: All AI components optimized for Tamil language processing

## Essential Development Commands

### Development Environment Setup
```bash
# Complete environment startup (recommended)
./scripts/dev/dev-start.sh

# Manual Docker services startup
docker compose -f docker-compose.dev.yml up -d

# Backend development (with hot reload)
source .venv/bin/activate
python -m uvicorn backend.main:app --reload

# Frontend development
cd app/nextjs
npm run dev
```

### Testing and Validation
```bash
# Run comprehensive test suite
python tests/run_all_tests.py

# Infrastructure health check
python tests/integration/test-infrastructure.py

# Database migrations
python -m alembic upgrade head

# Service status verification
docker compose -f docker-compose.dev.yml ps
```

### LLM Model Management
```bash
# Pull LLM models via Ollama
docker exec tamil-assistant-ollama ollama pull llama2

# Import custom GGUF models
docker exec tamil-assistant-ollama ollama create tamil-llama -f /models/Modelfile

# Switch to HuggingFace API mode
# Set USE_LOCAL_LLM=false in .env and configure HF_TOKEN
```

## Architecture Overview

### Core Pipeline Flow
```
User Voice → STT (Faster-Whisper) → RAG (pgVector + documents) →
LLM (Ollama/HuggingFace) → TTS (Google Cloud Chirp3 HD) → Audio Response
                                    ↓
            Database Session Storage (PostgreSQL + Redis cache)
```

### Technology Stack
- **Backend**: FastAPI + Python 3.10+ with async/await patterns
- **Frontend**: Next.js 16 + Material-UI + TypeScript (App Router)
- **Database**: PostgreSQL 16 + pgVector for 384-dimensional vector similarity
- **Storage**: MinIO for documents/audio + Redis for session caching
- **AI Pipeline**: LangChain + LangGraph state machines
- **Voice Processing**: Faster-Whisper (STT) + Google Cloud TTS (Tamil Chirp3 HD)
- **LLM**: Dual-mode Ollama (local) or HuggingFace API (serverless)

### Critical State Machines (LangGraph)

**Document Ingestion (backend/graphs/ingest_graph.py):**
File Upload → MinIO Storage → Text Extraction → Chunking → Embeddings → pgVector Storage → Status Update

**Voice Conversation (backend/graphs/chat_graph.py):**
Audio Input → STT → Context Retrieval → LLM Generation → TTS → Audio Output → Session Persistence → Loop

## Key Architecture Patterns

### Database-First Design
- **SQLAlchemy models** in `backend/database/models.py` define 10+ tables with full relationship mapping
- **pgVector integration** for 384-dimensional embeddings with similarity search
- **Alembic migrations** in `migrations/versions/` for schema evolution
- **Multi-tenant ready** with organization isolation and user role management

### Service Layer Pattern
- **Business logic** isolated in `backend/services/` (DocumentService, SessionService)
- **Infrastructure abstraction** in `backend/infrastructure/` with health monitoring
- **Retry mechanisms** with exponential backoff for all external service calls

### Real-Time Communication Architecture
- **WebSocket endpoints** in `backend/api/websocket.py` for live voice conversations
- **Binary audio streaming** with PCM format (16-bit, 16kHz) from frontend
- **Session persistence** combining PostgreSQL (permanent) + Redis (cache)
- **Connection management** with automatic reconnection and session recovery

### AI Pipeline Integration
- **LangGraph state machines** orchestrate complex multi-step AI workflows
- **Dual LLM backends**: Ollama (local) or HuggingFace API (serverless) via factory pattern
- **RAG implementation** with document chunking, embedding, and retrieval
- **Voice processing** with noise reduction, VAD, and Tamil-optimized TTS

### Frontend Architecture (Next.js 16)
```
app/nextjs/src/
├─ app/                   # App Router with Material-UI theming
├─ components/voice/      # RealTimeVoiceAssistant with Web Audio API
├─ components/admin/      # Document management and user administration
├─ services/api/          # API clients with proper error handling
└─ hooks/                 # Custom React hooks for state management
## Critical Configuration Patterns

### Environment-Based Configuration (settings.py)
- **Pydantic BaseSettings** with automatic environment variable binding
- **Docker-aware path detection** using `/.dockerenv` file presence
- **Auto-directory creation** ensures runtime directories exist on startup
- **Infrastructure URL construction** from components for flexibility

### Database Configuration Architecture
```python
# Multi-service configuration with fallbacks
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db  # Full URL (primary)
POSTGRES_PASSWORD=password                                # Component fallback
```

### Dual LLM Backend Pattern
```bash
# Toggle between local (Ollama) and cloud (HuggingFace) LLMs
USE_LOCAL_LLM=true   # Ollama at localhost:11435
USE_LOCAL_LLM=false  # HuggingFace API with HF_TOKEN
```

## Development Patterns

### Service Health Management
- All infrastructure services have **health checks** with exponential backoff
- **Connection pooling** with automatic retry for PostgreSQL, Redis, MinIO
- **Graceful degradation** when services are unavailable

### Audio Processing Pipeline
- **WebSocket binary streams** require PCM format (16-bit, 16kHz)
- **ScriptProcessorNode** for audio capture, NOT MediaRecorder
- **Voice Activity Detection** determines conversation turn boundaries

### Session Management Pattern
- **Dual persistence**: Redis (fast cache) + PostgreSQL (permanent storage)
- **Database sessions** with conversation turns and audio metadata
- **Session expiration** and cleanup with configurable TTL

## Common Development Issues & Solutions

### Backend Startup Problems
```bash
# Fix 1: RAG module import errors
# Symptom: ImportError for get_document_loader/get_text_chunker
# Solution: Wrapper functions are implemented, restart backend

# Fix 2: Database connection issues
python -c "import asyncio; from backend.database.connection import check_db_health; print(asyncio.run(check_db_health()))"

# Fix 3: Redis cache connectivity
python -c "import asyncio; from backend.cache.redis_client import check_redis_health; print(asyncio.run(check_redis_health()))"
```

### Audio Processing Issues
- **Wrong audio format**: Frontend must use ScriptProcessorNode with 16-bit PCM at 16kHz
- **WebSocket connection**: Audio streams are binary WebSocket messages, not HTTP uploads
- **Voice configuration changes**: Use `/admin/reset-tts` endpoint to reload TTS settings

### Session Management Patterns
- **Database sessions**: `backend/services/session_service.py` provides DatabaseSessionManager
- **Redis caching**: Sessions cached in Redis with PostgreSQL persistence
- **Session adapter**: Maintains backward compatibility with existing chat_graph.py

### Testing Infrastructure
```bash
# Complete test suite
python tests/run_all_tests.py

# Infrastructure validation only
python tests/integration/test-infrastructure.py

# Individual component tests
python tests/unit/test_session_service.py
```

## Project Status & Implementation Notes

### Current Implementation Status (November 2025)
- **✅ Database Foundation**: PostgreSQL + pgVector with 10 SQLAlchemy models
- **✅ Authentication System**: Complete JWT implementation with role-based access
- **✅ Infrastructure**: MinIO object storage + Redis caching + health monitoring
- **✅ Voice Pipeline**: Real-time WebSocket conversations with Tamil STT/TTS
- **🔄 Session Management**: Migrating from in-memory to database persistence
- **📋 Organization Platform**: Multi-tenant schema designed (150+ tasks planned)

### Tamil Voice Assistant Specifics
- **STT/TTS**: Optimized for Tamil language with Google Cloud Chirp3 HD voices
- **Audio Format**: WebSocket streams expect 16-bit PCM at 16kHz (use ScriptProcessorNode, not MediaRecorder)
- **Conversation Model**: Continuous dialogue like phone calls with session persistence
- **Language Support**: Tamil-first with multilingual embeddings for code-mixing

### Organization Platform (Future)
Multi-tenant transformation planned with 150+ tasks across 4 phases:
- Organization isolation, member management, billing integration
- Complete UI overhaul for organization context
- 12-16 week implementation timeline

## Critical Audio Implementation

**WebSocket Voice Requirements:**
```typescript
// ✅ CORRECT: Use ScriptProcessorNode for PCM audio
const audioContext = new AudioContext({ sampleRate: 16000 });
const processor = audioContext.createScriptProcessor(1024, 1, 1);
processor.onaudioprocess = (event) => {
  const pcmData = float32ToInt16(event.inputBuffer.getChannelData(0));
  websocket.send(pcmData); // Binary PCM data
};

// ❌ WRONG: MediaRecorder produces WebM/Opus (incompatible)
const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
```

---

For detailed implementation status, task tracking, and troubleshooting guides, see:
- **[README.md](README.md)** - Complete project overview and quick start
- **[tests/README.md](tests/README.md)** - Comprehensive testing framework guide
- **[TASKS.md](TASKS.md)** - Task tracking and project status
- **[docs/](docs/)** - Complete documentation hub