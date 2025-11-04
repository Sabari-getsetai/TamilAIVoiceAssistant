# Quick Start Guide - Tamil AI Voice Assistant

Get up and running with the RAG Q&A system in minutes!

## Prerequisites

1. **Python 3.9+** installed
2. **Docker** installed (for Ollama LLM)
3. **Git** (to clone the repository)

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Python Dependencies

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Download AI Models

```bash
# Download embedding, STT, and TTS models (~2-3GB)
python backend/models/download_models.py
```

### Step 3: Start Ollama LLM Server

```bash
# Start Ollama in Docker
docker compose -f docker-compose.dev.yml up -d

# Pull a model (llama2 is good for testing, ~4GB)
docker exec tamil-assistant-ollama ollama pull llama2

# Verify Ollama is running
docker exec tamil-assistant-ollama ollama list
```

## 🎯 Run the Demo

### Option 1: Complete RAG Q&A Demo (Recommended)

This demonstrates the entire pipeline working together:

```bash
python demo_rag_qa.py
```

**What it does:**
- Creates 4 sample Tamil documents about AI, Tamil language, technology, and healthcare
- Ingests documents using LangGraph workflow (loads → chunks → embeds → indexes)
- Answers 5 questions in Tamil and English using RAG
- Shows retrieved context and LLM-generated answers

**Expected output:**
```
🚀 Tamil AI Voice Assistant - RAG Q&A Demo
=========================================================================

📝 Step 1: Creating Sample Tamil Documents
  ✅ Created: ai_basics.txt (1234 chars)
  ✅ Created: tamil_language.txt (987 chars)
  ...

🔄 Step 2: Ingesting Documents with LangGraph Workflow
📂 Loading 4 documents...
✂️  Chunking documents...
🧮 Generating embeddings...
🗄️  Indexing in vector store...
✅ Ingestion completed!

💬 Step 3: Querying the RAG System
Question 1: செயற்கை நுண்ணறிவு என்றால் என்ன?
📚 Retrieved Context (4 documents):
  [1] செயற்கை நுண்ணறிவு என்பது...
💡 Answer:
செயற்கை நுண்ணறிவு (AI) என்பது கணினிகள் மூலம் மனித நுண்ணறிவை...
```

### Option 2: Test Individual Components

**Test RAG pipeline components:**
```bash
# Test embedding model
cd backend/rag
python embeddings.py

# Test text chunking
python chunking.py

# Test vector store
python vectorstore.py

# Test document loaders
python loaders.py

# Test complete RAG pipeline
python test_rag_pipeline.py
```

**Test LangGraph workflow:**
```bash
cd backend/graphs
python ingest_graph.py
```

**Test Admin API (requires FastAPI server running):**
```bash
# Terminal 1: Start API server
python -m uvicorn backend.main:app --reload

# Terminal 2: Run tests
python backend/api/test_admin_api.py
```

## 📚 What's Been Built (Phases 1-4)

### ✅ Phase 1-2: Foundation
- Project structure
- Settings management
- FastAPI application
- Ollama LLM integration
- Model download scripts

### ✅ Phase 3: RAG Pipeline
- Document loaders (PDF, DOCX, TXT)
- Text chunking (3 strategies)
- Embedding model (multilingual, Tamil-optimized)
- FAISS vector store
- Tamil-optimized prompts

### ✅ Phase 4: Document Ingestion API
- LangGraph workflow (load → chunk → embed → index)
- Admin API endpoints:
  - POST /admin/upload - Upload documents
  - POST /admin/ingest - Trigger ingestion
  - GET /admin/status/{session_id} - Check progress
  - GET /admin/documents - List indexed documents
  - DELETE /admin/documents/{doc_id} - Remove documents
  - GET /admin/stats - Vector store statistics

## 🎓 Next Steps

1. **Try your own documents:**
   ```bash
   # Copy your PDFs/DOCX/TXT files to:
   cp your_document.pdf data/docs/

   # Run the demo with your documents
   # (Modify demo_rag_qa.py to point to your files)
   ```

2. **Experiment with queries:**
   - Edit `demo_rag_qa.py` and add your own questions
   - Try Tamil, English, or code-mixed queries

3. **Explore the API:**
   ```bash
   # Start the server
   python -m uvicorn backend.main:app --reload

   # Visit http://localhost:8000/docs for interactive API docs
   ```

4. **Check the logs:**
   - All logs are in `data/logs/`
   - Vector stores saved in `data/faiss/`

## 🔧 Troubleshooting

**Ollama not connecting:**
```bash
# Check if Ollama is running
docker ps | grep ollama

# Check logs
docker compose -f docker-compose.dev.yml logs ollama

# Restart Ollama
docker compose -f docker-compose.dev.yml restart ollama
```

**Embedding model not found:**
```bash
# Re-download models
python backend/models/download_models.py
```

**Import errors:**
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 📖 Documentation

- **CLAUDE.md** - Detailed project documentation for Claude Code
- **TASKS.md** - Implementation task tracker (33% complete)
- **CHANGELOG.md** - Complete change history
- **PRD.md** - Product requirements document

## 🚧 Coming Next (Phases 5+)

- **Phase 5:** Speech Processing (STT, TTS, VAD)
- **Phase 6:** Conversational Chat API (WebSocket streaming)
- **Phase 7-9:** React PWA Frontend (Admin + Voice UI)
- **Phase 10+:** Integration, Testing, Deployment

## 💡 Tips

- Use **sentence-aware chunking** for best RAG results
- Increase `RETRIEVAL_K` in settings.py for more context
- Adjust `LLM_TEMPERATURE` for more/less creative answers
- Monitor vector store size with `/admin/stats` endpoint

---

**Questions?** Check CLAUDE.md for comprehensive documentation!
