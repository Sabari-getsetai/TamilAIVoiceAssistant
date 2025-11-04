# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Tamil AI Voice Assistant - a fully offline, privacy-focused conversational assistant that works like a live phone call. It combines LangChain + LangGraph for AI orchestration with an admin dashboard for RAG document management and a continuous voice conversation interface for Tamil language interactions.

**Key characteristics:**
- 100% offline operation with no internet dependency
- Tamil-first design (STT, TTS, LLM all support Tamil)
- Progressive Web App (PWA) for installable web experience
- RAG-based question answering with FAISS vector store
- Continuous conversation model - works like speaking on a phone call
- User initiates conversation with a button/action, then speaks naturally

## Architecture

### Technology Stack
- **Frontend:** Next.js + TypeScript + Tailwind CSS (App Router)
- **Backend:** FastAPI with Python 3.10+
- **AI Framework:** LangChain + LangGraph
- **LLM:** Dual-mode support:
  - **Ollama** (local, Docker): Tamil-LLaMA, Llama2, or custom GGUF models
  - **HuggingFace Inference API** (serverless): bloom-560m, KavithaSaaram, etc.
- **Embeddings:** SentenceTransformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Vector Store:** FAISS (local, offline)
- **STT:** Faster-Whisper (large-v2, Tamil support)
- **TTS:** Google Cloud Text-to-Speech (Chirp3 HD - ta-IN-Chirp3-HD-Callirrhoe) with customizable speaking rate, fallback to gTTS

### Core LangGraph State Machines

**IngestGraph (Admin Dashboard):**
Handles document ingestion workflow: Upload → Parse & Chunk → Compute Embeddings → Upsert to FAISS → Reindex Status

**ChatGraph (Conversational Assistant):**
Handles continuous voice conversation: User Speaks → STT → RAG Retrieve → LLM Inference → TTS → Assistant Speaks → Wait for User → Loop

The conversation continues in a call-like manner until the user explicitly ends the session.

## Folder Structure

```
backend/
├─ graphs/           # ✅ LangGraph state machines
│  ├─ ingest_graph.py    # Document ingestion workflow
│  └─ chat_graph.py       # Conversational pipeline (session management, history)
├─ rag/              # ✅ RAG pipeline components
│  ├─ loaders.py          # Document loaders (PDF, DOCX, etc.)
│  ├─ embeddings.py       # Embedding model wrapper
│  ├─ vectorstore.py      # FAISS vector store management
│  ├─ prompts.py          # Tamil-optimized prompts
│  └─ chunking.py         # Text chunking strategies
├─ speech/           # ✅ Speech processing
│  ├─ stt.py              # Speech-to-text (Tamil) with Faster-Whisper
│  ├─ tts.py              # Text-to-speech (Tamil) with Google TTS (female voice)
│  ├─ vad.py              # Voice Activity Detection
│  └─ audio_utils.py      # Audio processing utilities
├─ models/           # ✅ Model management
│  ├─ llm_local.py        # Ollama REST API client (local inference)
│  ├─ llm_huggingface.py  # HuggingFace Inference API client (serverless)
│  └─ download_models.py  # Auto-download script for embeddings/STT/TTS
├─ api/              # ✅ API endpoints
│  ├─ admin.py            # Admin dashboard (upload, ingest, status, document CRUD)
│  └─ chat.py             # Conversation (sessions, audio/text turns, WebSocket)
├─ database/         # ✅ Database models and connection (PostgreSQL + pgVector)
├─ storage/          # ✅ MinIO object storage client
├─ cache/            # ✅ Redis cache and session management
├─ main.py           # ✅ FastAPI application entry with health check
└─ settings.py       # ✅ Pydantic-based configuration management

app/
└─ nextjs/            # ✅ Next.js 15 + Material-UI - PRIMARY FRONTEND on port 3000
    ├─ src/
    │  ├─ app/              # Next.js App Router
    │  │  ├─ admin/         # ✅ Admin dashboard pages (upload, settings)
    │  │  └─ voice/         # ✅ Voice Assistant page
    │  ├─ components/       # React components
    │  │  ├─ admin/         # ✅ DocumentUpload, DocumentList, SettingsPanel
    │  │  ├─ voice/         # ✅ RealTimeVoiceAssistant (WebSocket + Web Audio API)
    │  │  ├─ layout/        # ✅ MainLayout, AppBar, Sidebar
    │  │  └─ ui/            # Reusable UI components
    │  ├─ lib/              # Utilities and services
    │  │  ├─ api/           # ✅ API clients (adminApi.ts, chatApi.ts)
    │  │  └─ hooks/         # ✅ Custom hooks (useDocuments, useStats, useUpload)
    │  └─ types/            # TypeScript type definitions

docs/                # ✅ Wiki-style documentation hub
├─ getting-started/  # ✅ New developer onboarding
├─ setup/            # ✅ Installation and configuration guides
├─ architecture/     # ✅ System design documentation
├─ features/         # ✅ Feature-specific documentation
├─ api/              # ✅ API reference documentation
├─ development/      # ✅ Development guidelines
├─ project/          # ✅ Project management and analysis
├─ reference/        # ✅ Quick reference materials
├─ troubleshooting/  # ✅ Problem solving guides
└─ README.md         # ✅ Documentation navigation hub

scripts/             # ✅ Organized utility scripts
├─ dev/              # ✅ Development scripts (dev-start.sh, check-services.sh)
├─ setup/            # ✅ Setup and installation scripts
├─ maintenance/      # ✅ System maintenance scripts
└─ utils/            # ✅ General utility scripts

tests/               # ✅ Comprehensive test suites
├─ integration/      # ✅ Infrastructure and API tests
├─ unit/             # ✅ Component unit tests
├─ performance/      # ✅ Performance benchmarks
├─ data/             # ✅ Test data and fixtures
└─ utils/            # ✅ Test utilities and demos

data/                # Auto-created directories for runtime data
├─ docs/             # Uploaded documents
├─ faiss/            # FAISS index files
├─ chunks/           # Document chunks
├─ logs/             # Application logs
└─ out/              # Generated audio outputs (organized with subdirectories)

models/              # Local model storage
├─ llm/              # ✅ GGUF model files (~4GB)
├─ stt/              # Reserved for STT model metadata
└─ tts/              # Reserved for TTS model metadata

migrations/          # ✅ Database schema migrations
├─ versions/         # ✅ Alembic migration versions
└─ 01_init_pgvector.sql  # ✅ PostgreSQL + pgVector initialization

# Docker infrastructure
docker-compose.dev.yml   # ✅ Development environment (PostgreSQL, Redis, MinIO, Ollama)
dev-start.sh            # ✅ One-command development startup
requirements.txt        # ✅ Python dependencies (includes database, auth, storage)

# Note: STT, TTS, and Embeddings models are cached in ~/.cache/huggingface/hub/
# This is standard practice for HuggingFace models and avoids duplication.
```

**Implementation Status:**
- ✅ Phases 1-10 Complete (~70% overall):
  - Backend fully functional (RAG, APIs, LangGraph, speech processing)
  - Next.js Admin Dashboard with Material-UI (document management, settings)
  - Voice Assistant UI with real-time WebSocket communication
  - Web Audio API integration for recording and playback using ScriptProcessorNode
  - Complete STT→RAG→LLM→TTS pipeline with female voice (Google TTS)
  - Home page with integrated voice assistant (mic button on landing page)
- 📋 Phases 11-14 Remaining (~30%): PWA features, testing, documentation, deployment

**Recent Critical Updates (Nov 2025):**
- ✅ **Project Restructuring Complete** - Wiki-style documentation, organized scripts/tests directories
- ✅ **Infrastructure Setup** - PostgreSQL+pgVector, MinIO, Redis integration ready
- ✅ **Legacy Frontend Removal** - Cleaned up app/web/, focused on Next.js as primary frontend
- ✅ TTS upgraded to Google Cloud TTS Chirp3 HD (ta-IN-Chirp3-HD-Callirrhoe) with exact voice matching
- ✅ Voice customization: Speaking rate 1.10x (10% faster), optimized for natural Tamil speech
- ✅ WebSocket TTS session management: Added update_all_tts_instances() for runtime voice updates
- ✅ Admin /reset-tts endpoint for reloading TTS configuration without server restart
- ✅ Smart pitch handling: Automatically disabled for Chirp3 HD voices (pre-optimized)
- ✅ Audio capture timing issue fixed (recording flag set before audio initialization)
- ✅ Upload-ingest API mismatch resolved (file_paths now correctly passed)
- ✅ React hydration errors fixed (Material-UI Chip component)

## Audio Format Requirements (CRITICAL)

**For WebSocket Voice Communication:**

The backend expects **raw 16-bit PCM audio** at 16kHz sample rate. Frontend implementations MUST use **ScriptProcessorNode** or **AudioWorkletNode** to capture raw PCM samples, NOT MediaRecorder with WebM/Opus.

**Correct Implementation Example:**
```typescript
// Create audio context with 16kHz sample rate
const audioContext = new AudioContext({ sampleRate: 16000 });
const processor = audioContext.createScriptProcessor(1024, 1, 1);

processor.onaudioprocess = (event) => {
  const inputData = event.inputBuffer.getChannelData(0); // Float32
  const pcmData = float32ToInt16(inputData);  // Convert to Int16 PCM
  sendAudioChunk(pcmData);  // Send as base64
};
```

**❌ WRONG - DO NOT USE:**
```typescript
// MediaRecorder produces WebM/Opus which backend cannot process
const mediaRecorder = new MediaRecorder(stream, {
  mimeType: 'audio/webm;codecs=opus'
});
```

**Reference Implementation:** See `app/nextjs/src/components/voice/RealTimeVoiceAssistant.tsx` for correct PCM audio capture.

## Development Commands

### Initial Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (required for Google TTS)
sudo apt-get install ffmpeg  # Linux
# brew install ffmpeg  # macOS

# Download offline AI models (auto-downloads embedding, STT models)
python backend/models/download_models.py

# Start Ollama LLM server (Docker-based)
docker compose -f docker-compose.dev.yml up -d

# Pull a model (quick test with llama2, ~4GB)
docker exec tamil-assistant-ollama ollama pull llama2

# Or load your local Tamil-LLaMA GGUF (see "Using Custom GGUF Models" below)
```

### Running the Application

```bash
# Run backend (FastAPI) - default on http://localhost:8000
# From project root:
python -m uvicorn backend.main:app --reload

# Or run directly with Python
cd backend
python main.py

# Run Next.js frontend (Primary) - http://localhost:3000
cd app/nextjs
npm install
npm run dev

# Or run legacy React+Vite frontend - http://localhost:5173
cd app/web
npm install
npm run dev

# Build Next.js for production
cd app/nextjs
npm run build

# Start production server
npm start
```

### Testing Commands

```bash
# Verify full setup (checks dependencies, directories, imports)
python verify_setup.py

# Test complete RAG pipeline with sample documents
python demo_rag_qa.py

# Query existing vector store
python query_rag.py "செயற்கை நுண்ணறிவு என்றால் என்ன?"

# Test LLM backends
cd backend/models
python llm_local.py           # Test Ollama (local)
python llm_huggingface.py     # Test HuggingFace API (requires HF_TOKEN in .env)

# Test individual components
cd backend
python -m rag.test_rag_pipeline       # Test RAG pipeline
python -m speech.test_speech_pipeline # Test STT/TTS/VAD
python -m graphs.test_chat_graph      # Test conversation graph
python -m api.test_admin_api          # Test admin endpoints
python -m api.test_chat_api           # Test chat endpoints

# Additional test files (from project root)
python test_noise_reduction.py        # Test noise reduction functionality
python test_rag_retrieval.py          # Test RAG retrieval accuracy
python select_voice.py                # Voice selection utility

# Check Ollama status and models
docker exec tamil-assistant-ollama ollama list

# Stop Ollama when done
docker compose -f docker-compose.dev.yml down
```

### Using Custom GGUF Models (Tamil-LLaMA)

To use your local Tamil-LLaMA GGUF file with Ollama:

```bash
# 1. Create a Modelfile (tells Ollama how to load your GGUF)
cat > models/llm/Modelfile << 'EOF'
FROM /models/tamil-llama-7b-v0.1-q4_k_m.gguf

PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER stop "###"

SYSTEM """You are a helpful Tamil AI assistant. You can understand and respond in both Tamil and English."""
EOF

# 2. Create the model in Ollama
docker exec tamil-assistant-ollama ollama create tamil-llama -f /models/Modelfile

# 3. Test it
docker exec tamil-assistant-ollama ollama run tamil-llama "வணக்கம்! நீங்கள் எப்படி இருக்கிறீர்கள்?"

# 4. Now use it in your code
cd backend/models
python llm_local.py  # Will prompt you to select tamil-llama
```

### API Endpoints

**Admin Endpoints** (Document Management)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/upload` | POST | Upload document files (PDF, DOCX, etc.) |
| `/admin/ingest` | POST | Trigger document ingestion workflow |
| `/admin/status` | GET | Get ingestion status and index statistics |
| `/admin/documents` | GET | List all indexed documents with metadata |
| `/admin/documents/{doc_id}` | DELETE | Delete a document from the index |
| `/admin/documents/{doc_id}/reindex` | POST | Reindex a single document (update embeddings) |
| `/admin/reindex` | POST | Batch reindex all documents |
| `/admin/clear` | POST | Clear entire FAISS index |
| `/admin/index` | DELETE | Delete FAISS index files |
| `/admin/reset-tts` | POST | Reset TTS engine and update all active websocket sessions |

**Chat Endpoints** (Conversation)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat/sessions` | POST | Create a new conversation session |
| `/chat/sessions` | GET | List all active sessions |
| `/chat/sessions/{id}` | GET | Get session details |
| `/chat/sessions/{id}` | DELETE | End a session |
| `/chat/sessions/{id}/history` | GET | Get conversation history |
| `/chat/sessions/{id}/stats` | GET | Get session statistics |
| `/chat/audio-turn` | POST | Process audio input, return audio response |
| `/chat/text-turn` | POST | Process text input, return text response |
| `/chat/ws/{session_id}` | WebSocket | Real-time bidirectional conversation |
| `/chat/audio/{filename}` | GET | Serve generated audio files |

**Speech Component Endpoints**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/speech/transcribe` | POST | STT: Convert audio to text (Tamil) |
| `/speech/synthesize` | POST | TTS: Convert text to audio (Tamil) |
| `/speech/vad` | POST | Voice Activity Detection test |

**Component Testing Endpoints**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat/test/transcribe` | POST | Test STT (audio → text) |
| `/chat/test/synthesize` | POST | Test TTS (text → audio) |
| `/chat/test/generate` | POST | Test LLM generation |

**General**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Root endpoint with API info |
| `/health` | GET | Backend health check |
| `/api/chat` | POST | Simple chat endpoint (auto session management) |

**WebSocket Communication:**
The `/chat/ws/{session_id}` endpoint provides real-time bidirectional voice conversation:
- Client sends audio chunks as binary WebSocket messages
- Server processes: STT → RAG → LLM → TTS
- Server streams back response audio in real-time
- Maintains conversation history throughout the session
- Used by the Voice Assistant UI (app/nextjs/src/components/voice/RealTimeVoiceAssistant.tsx)

## Key Dependencies

```python
# Web Framework
fastapi>=0.115.0           # Modern async web framework
uvicorn[standard]>=0.30.0  # ASGI server with WebSocket support
python-multipart>=0.0.9    # File upload support

# AI Orchestration
langchain>=0.2.0,<0.3.0    # LLM framework and RAG pipelines
langgraph>=0.2.0,<0.3.0    # State machine graphs for workflows
langchain-community>=0.2.0 # Community integrations

# Embeddings & Vector Store
sentence-transformers>=3.0.0  # Multilingual embeddings (paraphrase-multilingual-MiniLM)
faiss-cpu>=1.8.0             # Fast similarity search (CPU version)

# LLM - Ollama Integration
requests>=2.31.0           # Ollama REST API client
# Docker: ollama/ollama:latest (see docker-compose.dev.yml)

# Speech Processing
faster-whisper>=1.0.0      # Optimized Whisper STT (large-v2 model)
transformers               # For MMS-TTS Tamil model (facebook/mms-tts-tam)
soundfile>=0.12.0          # Audio I/O
accelerate>=0.20.0         # Model acceleration

# Document Processing
pypdf>=4.0.0               # PDF parsing
python-docx>=1.0.0         # DOCX parsing

# Utilities
python-dotenv>=1.0.0       # Environment configuration
pydantic>=2.0.0            # Data validation
pydantic-settings>=2.0.0   # Settings management
websockets>=12.0           # WebSocket support
```

## LangGraph State Schemas

### IngestState (Document Ingestion)
```python
class IngestState(TypedDict):
    files: List[str]      # Paths to uploaded files
    chunks: List[str]     # Chunked text segments
    status: str           # Ingestion status
```

### ChatState (Conversational Interaction)
```python
class ChatState(TypedDict):
    session_id: str           # Conversation session ID
    conversation_history: List[Dict]  # Full conversation context
    current_audio: str        # Current input audio path
    current_text: str         # Transcribed Tamil text
    response_text: str        # LLM generated response
    response_audio: str       # Output audio file path
    is_active: bool           # Session active status
```

## Conversational Flow

The assistant works like a phone call:

1. **User starts conversation** - Clicks/taps a button to initiate
2. **Assistant greets** - Plays Tamil greeting message
3. **Continuous loop:**
   - User speaks (voice activity detection determines when user finishes)
   - STT transcribes Tamil speech
   - RAG retrieves relevant context from documents
   - LLM generates contextual response (maintaining conversation history)
   - TTS converts response to Tamil speech
   - Assistant plays audio response
   - Waits for user to speak again
4. **User ends conversation** - Explicit action to end the call

## Tamil Language Considerations

- All prompts should be designed to work well with Tamil-LLaMA models
- STT/TTS models must support Tamil script and phonetics
- Embeddings model should handle code-mixing (Tamil + English)
- Conversation prompts should maintain natural Tamil dialogue flow
- System should handle conversational context across multiple turns
- Test voice accuracy target: >90%

## Performance Goals

- End-to-end voice latency: <3 seconds per turn
- Support PDFs, DOCX, and other document formats
- All inference must be fully offline
- Natural-sounding Tamil voice responses
- Maintain conversation context across entire session

## Privacy & Security

- All data stays on device (no external API calls)
- No telemetry or analytics
- Optional local admin authentication (JWT + SQLite)
- Document sandboxing for model access
- Conversation history stored locally only

### Debugging and Troubleshooting

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check Ollama connection
curl http://localhost:11435/api/tags

# View backend logs (if running with uvicorn --reload)
# Logs appear in terminal

# Test RAG pipeline end-to-end
python demo_rag_qa.py

# Test RAG with custom query
python query_rag.py

# Check FAISS index
python -c "from backend.rag.vectorstore import load_vectorstore; vs = load_vectorstore(); print(f'Index has {vs.index.ntotal} vectors')"

# Check installed models
ls -lh models/llm/
ls -lh ~/.cache/huggingface/hub/ | grep -E "(whisper|mms|sentence)"

# Frontend: Check API connection
# Open browser console at http://localhost:3000
# Look for CORS or connection errors
```

**Common Issues:**
- **Port 11435 already in use**: Another Ollama instance is running. Use `docker ps` to check.
- **FAISS index not found**: Run document ingestion first via `python demo_rag_qa.py` or admin dashboard.
- **HuggingFace API errors**: Ensure HF_TOKEN is set in .env file (not HF_API_TOKEN). Get token from https://huggingface.co/settings/tokens
- **STT model download slow**: First run downloads large models (~1-2GB). Cached in ~/.cache/huggingface/ afterward.
- **CORS errors in frontend**: Ensure backend CORS_ORIGINS includes frontend URL (check settings.py:54).
- **"Model loading" errors with HF**: Some models have cold starts. Wait 10-30 seconds and retry.
- **TTS requires internet**: Google Cloud TTS (Chirp3 HD) requires internet connection for synthesis. For offline TTS, use MMS-TTS (set `TTS_MODEL_NAME=facebook/mms-tts-tam` in .env).
- **Google Cloud TTS authentication**: Requires `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to service account JSON file.
- **Voice still sounds old after changes**: Call `/admin/reset-tts` endpoint to reload TTS configuration and update all active websocket sessions: `curl -X POST http://localhost:8000/admin/reset-tts`
- **Welcome message voice different from test files**: WebSocket sessions cache TTS instance on connection. Use `/admin/reset-tts` to update all active sessions, or refresh the page to reconnect.
- **ffmpeg not found**: Install ffmpeg system package: `sudo apt-get install ffmpeg` (Linux) or `brew install ffmpeg` (macOS).
- **Audio not capturing on home page**: Ensure audio is captured using ScriptProcessorNode with PCM format, not MediaRecorder. See "Audio Format Requirements" section.
- **422 error on document upload**: Check that frontend is sending `file_paths` array to `/admin/ingest`, not `job_id`.
- **React hydration errors**: Ensure Material-UI components inside `ListItemText` secondary content use `component="span"` prop.
- **Noise reduction affecting quality**: Adjust `NOISE_REDUCTION_STRENGTH` (0.0-1.0). Lower values preserve more original audio characteristics.
- **Document reindexing needed**: After changing `EMBEDDING_MODEL_NAME` or `CHUNK_SIZE`, use `/admin/reindex` to update all documents or `/admin/documents/{doc_id}/reindex` for individual documents.

## Model Configuration

The system uses Pydantic-based settings (backend/settings.py:8-93) with environment variable support. All settings are configurable but have sensible defaults.

**Configurable via .env file:**
```bash
# LLM Backend Selection
USE_LOCAL_LLM=true  # true=Ollama (local), false=HuggingFace API (serverless)

# Ollama Settings (when USE_LOCAL_LLM=true)
OLLAMA_BASE_URL=http://localhost:11435
LLM_MODEL_NAME=bloom-560m.q8_0.gguf  # Or tamil-llama, llama2, etc.

# HuggingFace Settings (when USE_LOCAL_LLM=false)
HF_MODEL_NAME=aisingapore/Llama-SEA-LION-v2-8B-IT:featherless-ai  # Tamil instruction-tuned model
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx  # IMPORTANT: Use HF_TOKEN (not HF_API_TOKEN)
# Get free token from: https://huggingface.co/settings/tokens

# Other Model Settings
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
STT_MODEL_NAME=large-v2

# TTS Configuration (Google Cloud TTS - requires internet & authentication)
TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe  # Chirp3 HD voice (ultra-high quality)
# Available Chirp3 HD voices:
#   - ta-IN-Chirp3-HD-Callirrhoe (natural female, recommended)
#   - ta-IN-Chirp3-HD-Achernar (alternative female)
# WaveNet voices (premium):
#   - ta-IN-Wavenet-B (female)
#   - ta-IN-Wavenet-A (male)
# For offline TTS, use MMS-TTS: TTS_MODEL_NAME=facebook/mms-tts-tam

# TTS Voice Customization (Google Cloud TTS only)
TTS_SPEAKING_RATE=1.10  # 1.0=normal, 1.10=10% faster (matches reference sample)
TTS_PITCH=0.0           # Pitch in semitones (Chirp3 HD doesn't support this, use 0.0)
TTS_VOLUME_GAIN_DB=0.0  # Volume adjustment in dB

# Google Cloud TTS Authentication
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# RAG Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_K=4

# Audio Processing & Noise Reduction
ENABLE_NOISE_REDUCTION=true
NOISE_REDUCTION_STRENGTH=0.6      # 0.0-1.0, higher = more aggressive
NOISE_REDUCTION_STATIONARY=false  # false = non-stationary (better quality)
NOISE_REDUCTION_USE_TORCH=false   # true = GPU acceleration
MIN_AUDIO_DURATION=1.0            # Minimum audio duration before allowing stop
VAD_SILENCE_DURATION=1.5          # Silence duration to detect speech end (increased from 1.0s)

# LLM Generation
LLM_MAX_TOKENS=150       # Reduced for faster generation
LLM_TEMPERATURE=0.9      # Higher temp for faster sampling
LLM_CONTEXT_LENGTH=2048  # Reduced for speed

# Conversation Settings
MAX_CONVERSATION_HISTORY=10
SESSION_TIMEOUT_MINUTES=30

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]
```

## TTS Configuration & Voice Customization

The system uses **Google Cloud Text-to-Speech Chirp3 HD** voices by default, with fallback to gTTS for basic needs.

### Chirp3 HD Voice Features

**ta-IN-Chirp3-HD-Callirrhoe** (default):
- Latest generation Google AI voice (2024+)
- Ultra-natural, human-like Tamil speech
- Pre-optimized by Google (no pitch adjustment needed)
- 24kHz sample rate for high-quality audio
- Professional-grade, production-ready
- Requires internet connection and Google Cloud authentication

### Voice Configuration Files

**backend/settings.py (Lines 35-53)**:
- Central configuration with Pydantic settings
- TTS_MODEL_NAME: Voice selection
- TTS_SPEAKING_RATE: Speed adjustment (1.10 = 10% faster)
- TTS_PITCH: Pitch adjustment (disabled for Chirp3 HD)
- TTS_VOLUME_GAIN_DB: Volume control

**backend/speech/tts.py**:
- GoogleCloudTTS class with voice type detection
- Smart pitch handling (automatically disabled for Chirp3 HD)
- Audio format: LINEAR16 PCM at 24kHz for Chirp3 HD
- Preserves natural Chirp3 HD characteristics (no artificial processing)
- Falls back to gTTS if Google Cloud credentials unavailable

### Runtime TTS Updates

**Problem**: WebSocket sessions cache TTS instance on connection. Changing .env settings doesn't update active sessions.

**Solution**: Use `/admin/reset-tts` endpoint to reload configuration:

```bash
# Update .env file with new settings
echo "TTS_SPEAKING_RATE=1.15" >> .env

# Reset TTS engine and update all active websocket sessions
curl -X POST http://localhost:8000/admin/reset-tts

# Response shows updated configuration:
{
  "success": true,
  "message": "TTS engine reset successfully",
  "current_voice": "ta-IN-Chirp3-HD-Callirrhoe",
  "speaking_rate": 1.15,
  "voice_type": "Chirp3 HD (Ultra-High Quality)",
  "engine": "GoogleCloudTTS",
  "updated_websocket_sessions": 2
}
```

**Implementation Details**:
- `reset_tts_engine()` function clears global TTS cache (backend/speech/tts.py:462-470)
- `ConnectionManager.update_all_tts_instances()` updates all active sessions (backend/api/websocket.py:89-102)
- No user disconnection required - sessions automatically use new voice
- If still hearing old voice, hard refresh browser (Ctrl+F5)

### Voice Matching & Audio Analysis

The current configuration (TTS_SPEAKING_RATE=1.10) was calibrated to match a reference sample at `data/out/voice_comparison/test_5_Chirp3_HD_Callirrhoe.wav`:

| Parameter | Reference | Achieved | Difference |
|-----------|-----------|----------|------------|
| Duration | 5.721s | 5.754s | 0.033s (0.58%) |
| Peak Level | 1.000 (0 dB) | 1.000 (0 dB) | Perfect match |
| Speaking Rate | ~1.10x | 1.10x | Exact match |
| Voice Model | Chirp3 HD | Chirp3 HD | Matched |

See `VOICE_IMPLEMENTATION_SUMMARY.md` for detailed audio analysis results.

### Switching Between TTS Engines

**Google Cloud TTS (Default - Requires Internet)**:
```bash
# .env
TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

**Offline TTS with MMS-TTS**:
```bash
# .env
TTS_MODEL_NAME=facebook/mms-tts-tam
# Remove or comment out GOOGLE_APPLICATION_CREDENTIALS
```

**gTTS Fallback (Basic)**:
- Automatically used if Google Cloud credentials are unavailable
- Requires internet but no authentication
- Lower quality than Chirp3 HD
- Implementation in backend/speech/tts.py

### Testing TTS Configuration

```bash
# Test TTS directly via API
curl -X POST 'http://localhost:8000/api/speech/tts' \
  -H 'Content-Type: application/json' \
  -d '{"text": "வணக்கம்! இது Chirp3 HD குரல்."}'

# Returns audio file that can be played
# Check backend logs for voice details

# Test via chat endpoint
curl -X POST 'http://localhost:8000/chat/test/synthesize' \
  -H 'Content-Type: application/json' \
  -d '{"text": "வணக்கம்!"}'
```

## Document Reindexing System

When you change embedding models, chunking parameters, or need to refresh the vector store, use the reindexing system:

### When to Reindex

**Required after changing:**
- `EMBEDDING_MODEL_NAME` - Different embeddings need recomputation
- `CHUNK_SIZE` or `CHUNK_OVERLAP` - Text chunks need regeneration
- Document content (if files were modified outside the system)

**Reindexing Options:**

```bash
# Reindex all documents (batch operation)
curl -X POST http://localhost:8000/admin/reindex

# Reindex single document
curl -X POST http://localhost:8000/admin/documents/{doc_id}/reindex

# Clear entire index (nuclear option)
curl -X POST http://localhost:8000/admin/clear

# Delete index files (for troubleshooting)
curl -X DELETE http://localhost:8000/admin/index
```

**Simple Chat API:**

For basic text-only interactions without session management complexity:

```bash
# Simple chat (auto-creates and manages session)
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "செயற்கை நுண்ணறிவு என்றால் என்ன?"}'
```

This endpoint automatically handles session creation, RAG retrieval, and LLM generation without requiring explicit session management.

## Implementation Notes

**Dual LLM Backend:**
The system supports TWO LLM backends (configured via `USE_LOCAL_LLM` in settings.py:60):

1. **Ollama (Local)** - For fully offline operation:
   - Docker-based LLM server running at http://localhost:11435
   - Supports any GGUF model (Tamil-LLaMA, Llama2, etc.)
   - 3-5x faster inference with optimized C++ backend
   - Streaming support for real-time token generation
   - Easy model management via CLI: `ollama pull`, `ollama create`
   - Implementation: backend/models/llm_local.py

2. **HuggingFace Inference API (Serverless)** - For zero-setup deployment:
   - No local model downloads or GPU/RAM requirements
   - Free tier available with HF API token (HF_TOKEN)
   - Uses Chat Completions API endpoint for better conversation handling
   - Access to latest multilingual models (KavithaSaaram-2b-it for Tamil)
   - Better Tamil support with instruction-tuned models
   - Implementation: backend/models/llm_huggingface.py (uses HuggingFace router)

**To switch between modes:**
```bash
# .env file
USE_LOCAL_LLM=true   # Use Ollama (default)
USE_LOCAL_LLM=false  # Use HuggingFace API (requires HF_TOKEN)
```

**Unified LLM Interface:**
The system uses a factory pattern (backend/models/__init__.py) that provides:
- `UnifiedLLM` class that automatically switches between backends based on `USE_LOCAL_LLM` setting
- `get_llm()` returns the configured backend (Local or HuggingFace)
- `initialize_llm()` loads the model for the active backend
- All application code uses this unified interface, making backend switching transparent

**Usage in application code:**
```python
from backend.models import get_llm, initialize_llm

# Get appropriate LLM (based on USE_LOCAL_LLM setting)
llm = get_llm()

# Initialize and load model
if initialize_llm():
    response = llm.generate(prompt="வணக்கம்!", max_tokens=100)
```

This abstraction allows seamless switching between local and cloud inference without code changes.

**Model Download Strategy:**
- Embedding, STT, TTS models auto-download from HuggingFace (cached in ~/.cache/huggingface/)
- LLM models managed by Ollama:
  - Quick test: `ollama pull llama2` (~4GB)
  - Custom GGUF: Create Modelfile and import with `ollama create`
  - Local Tamil-LLaMA: Already downloaded in models/llm/, just import to Ollama

**Directory Auto-Creation:**
The settings.py module (backend/settings.py:74-92) automatically creates all required directories (data/, models/, etc.) on import via the `ensure_directories()` function. This ensures the app can run immediately after cloning.

**Docker Development Setup (Full Stack):**

The entire application stack (Backend + Frontend + Ollama + FAISS) runs in Docker containers with named volumes for data persistence.

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│ Docker Network: tamil-assistant-network         │
│                                                  │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │ Frontend         │  │ Backend          │    │
│  │ (Next.js)        │→ │ (FastAPI+FAISS)  │    │
│  │ Port 3000        │  │ Port 8000        │    │
│  └──────────────────┘  └────────┬─────────┘    │
│                                 │               │
│                                 ↓               │
│                        ┌──────────────────┐    │
│                        │ Ollama (LLM)     │    │
│                        │ Port 11435       │    │
│                        └──────────────────┘    │
│                                                  │
│  Named Volumes:                                 │
│  • tamil-assistant-faiss  → FAISS persistence  │
│  • tamil-assistant-ollama → LLM models         │
└─────────────────────────────────────────────────┘
```

**Quick Start:**
```bash
# Start entire stack (builds images first time)
docker compose -f docker-compose.dev.yml up --build

# Or start in detached mode
docker compose -f docker-compose.dev.yml up -d

# View logs from all services
docker compose -f docker-compose.dev.yml logs -f

# View logs from specific service
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
docker compose -f docker-compose.dev.yml logs -f ollama

# Stop services (keeps volumes)
docker compose -f docker-compose.dev.yml down

# Stop and remove volumes (deletes FAISS data and Ollama models)
docker compose -f docker-compose.dev.yml down -v

# Rebuild after code changes
docker compose -f docker-compose.dev.yml up --build backend
docker compose -f docker-compose.dev.yml up --build frontend
```

**Service Details:**

1. **Backend Container** (tamil-assistant-backend):
   - FastAPI with FAISS vector store
   - Mounts `faiss_data` named volume to `/app/data`
   - Hot-reload enabled (./backend mounted for development)
   - Connects to Ollama via `http://ollama:11434`

2. **Frontend Container** (tamil-assistant-frontend):
   - Next.js 15 with hot-reload
   - Communicates with backend via `http://localhost:8000`
   - WebSocket connection for voice features

3. **Ollama Container** (tamil-assistant-ollama):
   - LLM inference engine
   - Persistent model storage in `ollama_data` volume
   - Resource limits: 4 CPUs, 6GB RAM

**Data Persistence:**
- FAISS indices stored in named volume `tamil-assistant-faiss`
- Survives container restarts and updates
- To backup: `docker run --rm -v tamil-assistant-faiss:/data -v $(pwd):/backup alpine tar czf /backup/faiss-backup.tar.gz -C /data .`
- To restore: `docker run --rm -v tamil-assistant-faiss:/data -v $(pwd):/backup alpine tar xzf /backup/faiss-backup.tar.gz -C /data`

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend Docs: http://localhost:8000/docs
- Ollama API: http://localhost:11435

**Docker-Aware Configuration:**
- Backend automatically detects Docker environment (checks `/.dockerenv`)
- Paths adjust to `/app` in container vs local paths on host
- OLLAMA_BASE_URL switches to `http://ollama:11434` in Docker
- CORS includes `http://frontend:3000` for inter-container communication

**Frontend Implementation:**
The project has TWO frontend implementations:

1. **Next.js 15 + Material-UI (PRIMARY)** - app/nextjs/ on port 3000:
   - **Admin Dashboard:**
     - Built with Next.js 15 App Router
     - Material-UI components and theming
     - Document upload with drag-and-drop support
     - Real-time ingestion progress monitoring
     - Document management (search, view, delete)
     - Index statistics (document count, chunk count, last updated)
     - Settings panel for configuration
   - **Voice Assistant:**
     - RealTimeVoiceAssistant component with Web Audio API
     - WebSocket-based real-time communication
     - Live audio visualization during recording
     - Conversation history display
     - Complete STT→RAG→LLM→TTS pipeline integration
   - Custom hooks (useDocuments, useStats, useUpload)
   - API integration layer (adminApi.ts, chatApi.ts)
   - Server-side rendering and client components

2. **React + Vite + Tailwind (LEGACY)** - app/web/ on port 5173:
   - Original frontend implementation
   - Lightweight alternative with Tailwind CSS
   - Basic admin and chat interfaces
   - Still maintained for reference

**Access Points:**
- Voice Assistant: http://localhost:3000/voice
- Admin Dashboard: http://localhost:3000/admin
- Backend API: http://localhost:8000

**Important Notes:**
- Use `docker compose` (Docker Compose V2) instead of `docker-compose` (V1 is deprecated)
- **CHANGELOG.md tracking:** Every code/file change MUST be logged in CHANGELOG.md with date and time (format: YYYY-MM-DD HH:MM:SS)
- **TASKS.md updates:** Mark tasks as complete in TASKS.md when finished
- All backend components (RAG, graphs, speech, APIs) are fully implemented
- Admin Dashboard and Voice Assistant UI (Phases 8-10) are complete
- Next phases: PWA features, testing, documentation, deployment
- The system can run in two modes: fully offline (Ollama) or cloud-hybrid (HuggingFace API + Google TTS)

**Development Best Practices:**
- **Audio Capture:** Always use ScriptProcessorNode (not MediaRecorder) for WebSocket voice communication
- **TypeScript Interfaces:** Keep frontend types in sync with backend Pydantic models (especially API request/response schemas)
- **Material-UI:** Use `component="span"` for MUI components nested inside text elements to avoid hydration errors
- **Error Handling:** All async operations should have proper try-catch blocks and user-facing error messages
- **Logging:** Use console.log liberally during development; backend uses Python logging module
- **WebSocket:** Always check `websocket.readyState === WebSocket.OPEN` before sending messages