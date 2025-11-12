# Docker Setup Guide - Tamil AI Voice Assistant

This guide covers running the Tamil AI Voice Assistant in a fully containerized environment using Docker Compose.

## Overview

The application runs as a multi-container stack:
- **Backend**: FastAPI + FAISS vector store (port 8000)
- **Frontend**: Next.js voice UI (port 3000)
- **Ollama**: LLM inference engine (port 11435)

All services communicate via a Docker bridge network, with persistent data stored in named volumes.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose V2 (comes with Docker Desktop)
- 8GB+ RAM available for Docker
- 10GB+ free disk space

**Check your installation:**
```bash
docker --version
# Docker version 20.10.0 or higher

docker compose version
# Docker Compose version v2.0.0 or higher
```

## Quick Start

### 1. Clone and Setup

```bash
cd /home/sabari/Sabari/GetSetAI/Projects/TamilAIVoiceAssistant

# Verify required files exist
ls -la Dockerfile docker-compose.dev.yml app/nextjs/Dockerfile

# (Optional) Create credentials directory for Google Cloud TTS
mkdir -p credentials
# Place your service-account-key.json in credentials/ directory
```

### 2. Start the Full Stack

```bash
# Build and start all services (first time)
docker compose -f docker-compose.dev.yml up --build

# Or start in detached mode (background)
docker compose -f docker-compose.dev.yml up -d

# View logs in real-time
docker compose -f docker-compose.dev.yml logs -f
```

**First startup takes 2-5 minutes** to:
- Build Docker images
- Install Python dependencies (~500MB)
- Install Node.js dependencies (~200MB)
- Download AI models (STT, embeddings)

### 3. Verify Services

Open in your browser:
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Check all containers are running:
```bash
docker compose -f docker-compose.dev.yml ps

# Should show:
# tamil-assistant-backend    running   0.0.0.0:8000->8000/tcp
# tamil-assistant-frontend   running   0.0.0.0:3000->3000/tcp
# tamil-assistant-ollama     running   0.0.0.0:11435->11434/tcp
```

### 4. Pull LLM Model (First Time Only)

```bash
# Pull a lightweight model for testing
docker exec tamil-assistant-ollama ollama pull llama2

# Or use Tamil-optimized model (larger)
docker exec tamil-assistant-ollama ollama pull tamil-llama

# List available models
docker exec tamil-assistant-ollama ollama list
```

## Common Operations

### Viewing Logs

```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
docker compose -f docker-compose.dev.yml logs -f ollama

# Last 100 lines
docker compose -f docker-compose.dev.yml logs --tail=100 backend
```

### Stopping and Starting

```bash
# Stop all services (keeps data)
docker compose -f docker-compose.dev.yml down

# Start again (uses existing volumes)
docker compose -f docker-compose.dev.yml up -d

# Stop and remove volumes (DELETES ALL DATA)
docker compose -f docker-compose.dev.yml down -v
```

### Rebuilding After Code Changes

```bash
# Rebuild backend only
docker compose -f docker-compose.dev.yml up --build backend

# Rebuild frontend only
docker compose -f docker-compose.dev.yml up --build frontend

# Rebuild all services
docker compose -f docker-compose.dev.yml up --build

# Force complete rebuild (no cache)
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up
```

### Accessing Container Shells

```bash
# Backend container (Python/FastAPI)
docker exec -it tamil-assistant-backend bash

# Frontend container (Node/Next.js)
docker exec -it tamil-assistant-frontend sh

# Ollama container
docker exec -it tamil-assistant-ollama bash

# Run Python commands in backend
docker exec -it tamil-assistant-backend python -c "from backend.rag.vectorstore import load_vectorstore; print(load_vectorstore())"
```

## Data Persistence

### Named Volumes

The stack uses Docker named volumes for persistent data:

1. **tamil-assistant-faiss**: FAISS vector indices
   - Location: `/app/data` in backend container
   - Contains: `faiss/`, `docs/`, `chunks/`, `logs/`, `out/`

2. **tamil-assistant-ollama**: LLM models
   - Location: `/root/.ollama` in ollama container
   - Contains: Downloaded GGUF models

### Inspecting Volumes

```bash
# List all volumes
docker volume ls | grep tamil-assistant

# Inspect FAISS volume
docker volume inspect tamil-assistant-faiss

# Check size of volumes
docker system df -v | grep tamil-assistant
```

### Backup and Restore

**Backup FAISS data:**
```bash
# Create backup tarball
docker run --rm \
  -v tamil-assistant-faiss:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/faiss-backup-$(date +%Y%m%d).tar.gz -C /data .

# Backup is saved to: ./faiss-backup-YYYYMMDD.tar.gz
```

**Restore FAISS data:**
```bash
# Stop services first
docker compose -f docker-compose.dev.yml down

# Restore from backup
docker run --rm \
  -v tamil-assistant-faiss:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/faiss-backup-20251101.tar.gz -C /data

# Start services
docker compose -f docker-compose.dev.yml up -d
```

**Backup Ollama models:**
```bash
docker run --rm \
  -v tamil-assistant-ollama:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/ollama-backup-$(date +%Y%m%d).tar.gz -C /data .
```

## Development Workflow

### Hot Reload

Both backend and frontend support hot-reload during development:

**Backend**: Edit files in `./backend/`, changes auto-reload in container
- Uvicorn watches for file changes
- Logs show: "Detected file change, reloading..."

**Frontend**: Edit files in `./app/nextjs/`, Next.js auto-rebuilds
- Fast Refresh updates UI without full reload
- Logs show: "Compiled successfully"

### Environment Variables

Edit `.env` file in project root (create if not exists):

```bash
# .env
TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe
TTS_SPEAKING_RATE=1.10
OLLAMA_BASE_URL=http://ollama:11434
USE_LOCAL_LLM=true
HF_TOKEN=hf_xxxxxxxxxxxxx
```

Restart backend to apply:
```bash
docker compose -f docker-compose.dev.yml restart backend
```

### Using Different LLM Models

**Switch to HuggingFace API** (no local GPU needed):
```bash
# Edit .env
USE_LOCAL_LLM=false
HF_TOKEN=hf_your_token_here
HF_MODEL_NAME=akdiwahar/KavithaSaaram-2b-it

# Restart backend
docker compose -f docker-compose.dev.yml restart backend
```

**Use local Ollama** (default):
```bash
# Edit .env
USE_LOCAL_LLM=true

# Pull model
docker exec tamil-assistant-ollama ollama pull llama2

# Restart backend
docker compose -f docker-compose.dev.yml restart backend
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker compose -f docker-compose.dev.yml logs backend
docker compose -f docker-compose.dev.yml logs frontend
```

**Common issues:**
- Port already in use: Change ports in `docker-compose.dev.yml`
- Out of memory: Increase Docker memory limit (Docker Desktop → Settings → Resources)
- Build failures: Run `docker compose -f docker-compose.dev.yml build --no-cache`

### Backend Can't Connect to Ollama

**Verify Ollama is running:**
```bash
docker exec tamil-assistant-ollama curl -f http://localhost:11434/
```

**Check network:**
```bash
docker network inspect tamil-assistant-network

# All three containers should be listed under "Containers"
```

**Test connection from backend:**
```bash
docker exec tamil-assistant-backend curl -f http://ollama:11434/
```

### FAISS Index Not Found

**Check volume:**
```bash
docker exec tamil-assistant-backend ls -la /app/data/faiss/
```

**Upload documents via UI:**
1. Go to http://localhost:3000/admin
2. Upload PDF/DOCX files
3. Click "Ingest Documents"
4. Check backend logs for progress

**Verify index:**
```bash
docker exec tamil-assistant-backend python -c "
from backend.rag.vectorstore import load_vectorstore
vs = load_vectorstore()
print(f'Index has {vs.index.ntotal} vectors')
"
```

### Frontend Can't Connect to Backend

**Check backend is running:**
```bash
curl http://localhost:8000/health
```

**Check CORS configuration:**
```bash
docker exec tamil-assistant-backend python -c "
from backend.settings import settings
print(settings.CORS_ORIGINS)
"
# Should include: http://localhost:3000, http://frontend:3000
```

**Check browser console** (F12):
- Look for CORS errors
- Look for WebSocket connection errors
- Verify API_URL is correct

### WebSocket Connection Fails

**Check if backend WebSocket is accessible:**
```bash
# Install wscat: npm install -g wscat
wscat -c ws://localhost:8000/ws/voice/test-session

# Should connect without errors
```

**Frontend environment variable:**
```bash
docker exec tamil-assistant-frontend env | grep NEXT_PUBLIC

# Should show:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Slow Performance

**Check resource usage:**
```bash
docker stats

# Look for:
# - High CPU/memory usage
# - Container restarts
```

**Reduce Ollama memory** (if needed):
Edit `docker-compose.dev.yml`:
```yaml
ollama:
  deploy:
    resources:
      limits:
        memory: 4G  # Reduced from 6G
```

**Use smaller LLM model:**
```bash
docker exec tamil-assistant-ollama ollama pull llama2:7b-chat
# Instead of larger 13B or 70B models
```

## Production Deployment

For production, create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    command: ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    # Remove --reload flag
    # Add health checks
    # Add resource limits

  frontend:
    build: ./app/nextjs
    command: ["npm", "start"]
    # Uses production build
    # Requires npm run build first
```

**Build for production:**
```bash
cd app/nextjs
docker run --rm -v $(pwd):/app -w /app node:18-alpine npm run build

docker compose -f docker-compose.prod.yml up --build -d
```

## Useful Commands Reference

```bash
# Full stack management
docker compose -f docker-compose.dev.yml up -d          # Start all
docker compose -f docker-compose.dev.yml down           # Stop all
docker compose -f docker-compose.dev.yml restart        # Restart all
docker compose -f docker-compose.dev.yml ps             # List containers

# Individual services
docker compose -f docker-compose.dev.yml up backend     # Start backend only
docker compose -f docker-compose.dev.yml restart frontend  # Restart frontend

# Logs
docker compose -f docker-compose.dev.yml logs -f        # All logs
docker compose -f docker-compose.dev.yml logs backend   # Backend logs

# Cleanup
docker compose -f docker-compose.dev.yml down -v        # Remove volumes
docker system prune -a                                  # Clean all Docker data

# Volume management
docker volume ls                                        # List volumes
docker volume inspect tamil-assistant-faiss            # Inspect volume
docker volume rm tamil-assistant-faiss                 # Delete volume

# Exec commands
docker exec -it tamil-assistant-backend bash           # Backend shell
docker exec tamil-assistant-backend python backend/models/llm_local.py  # Run script
docker exec tamil-assistant-ollama ollama list         # List models
```

## Next Steps

1. **Upload Documents**: Go to http://localhost:3000/admin to upload and index documents
2. **Test Voice Assistant**: Visit http://localhost:3000/voice to try conversation
3. **Configure TTS**: Edit `.env` to customize voice settings
4. **Pull LLM Models**: Use `ollama pull` to download language models
5. **Read API Docs**: Check http://localhost:8000/docs for API reference

## Support

For issues:
- Check logs: `docker compose -f docker-compose.dev.yml logs -f`
- Review CLAUDE.md for architecture details
- See docs/project/changelog.md for recent changes
- Check GitHub issues for known problems

**Common Documentation Files:**
- `CLAUDE.md` - Complete project documentation
- `VOICE_IMPLEMENTATION_SUMMARY.md` - TTS voice setup
- `docs/project/changelog.md` - Version history
- `README.md` - Project overview
