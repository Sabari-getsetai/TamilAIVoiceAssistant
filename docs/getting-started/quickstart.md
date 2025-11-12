# Quick Start Guide - Tamil AI Voice Assistant

Get up and running with the organization-based Tamil AI Voice Assistant platform in minutes! This guide covers the new multi-tenant organization platform with email verification, member management, and role-based access control.

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: At least 10GB free space
- **Network**: Internet connection for downloading models and dependencies

### Required Software
1. **Python 3.9+** installed
2. **Docker & Docker Compose** installed (for services)
3. **Git** (to clone the repository)
4. **Node.js 18+** (for frontend development)
5. **PostgreSQL** (for organization data)

### Optional for Production
- **Email Service** (Gmail, SendGrid, AWS SES) for organization invitations
- **Google Cloud TTS** credentials for high-quality voice synthesis

## 🚀 Quick Setup (10 minutes)

### Step 1: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Key settings for organization platform:
ENABLE_ORGANIZATION_PLATFORM=true
ENABLE_ORGANIZATION_REGISTRATION=true
JWT_SECRET_KEY=your-super-secret-jwt-key-here
DATABASE_URL=postgresql+asyncpg://tamil_user:password@localhost:5432/tamil_assistant
```

### Step 2: Install Dependencies

```bash
# Backend dependencies
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend dependencies (optional for development)
cd app/nextjs
npm install
cd ../..
```

### Step 3: Database Setup

```bash
# Start PostgreSQL and other services
docker compose -f docker-compose.dev.yml up -d postgres redis minio

# Run database migrations
alembic upgrade head

# Verify database connection
python -c "from backend.database.connection import get_db_info; print(get_db_info())"
```

### Step 4: Download AI Models

```bash
# Download embedding, STT, and TTS models (~2-3GB)
python backend/models/download_models.py
```

### Step 5: Start Services

```bash
# Start Ollama LLM server
docker compose -f docker-compose.dev.yml up -d ollama

# Pull a model (sarvam-2b-v0.5 recommended for Tamil)
docker exec tamil-assistant-ollama ollama pull sarvam-2b-v0.5

# Verify Ollama is running
docker exec tamil-assistant-ollama ollama list
```

### Step 6: Configure Email Service (Optional for Development)

For organization invitations and email verification:

```bash
# Add to your .env file:
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME="Tamil AI Assistant"

# Enable email features
ENABLE_EMAIL_VERIFICATION=true
ENABLE_EMAIL_INVITATIONS=true
```

### Step 7: First-Time Organization Setup

After starting the platform, you'll need to create your first organization:

1. **Register a new user account** at http://localhost:3000/register
2. **Verify your email** (if email verification is enabled)
3. **Create your organization** - you'll be redirected to organization setup
4. **Invite team members** (optional) via email invitations
5. **Start using the platform** with organization-scoped features

## 🎯 Run the Platform

### Option 1: Start the Full Platform (Recommended)

Start both backend and frontend for the complete organization platform experience:

```bash
# Terminal 1: Start backend API server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend development server
cd app/nextjs
npm run dev
```

**Access the platform:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Option 2: Organization Platform Demo

Test the organization features with authentication:

```bash
# Start the backend server first
python -m uvicorn backend.main:app --reload

# In another terminal, test organization APIs
python backend/api/test_auth_endpoints.py
```

**What it demonstrates:**
- User registration and authentication
- Organization creation and management
- Member invitation and role management
- Organization-scoped document management
- Multi-tenant data isolation

### Option 3: Legacy RAG Q&A Demo

For testing the core RAG pipeline without organization features:

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

### Option 4: Test Individual Components

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

**Test organization APIs:**
```bash
# Terminal 1: Start API server
python -m uvicorn backend.main:app --reload

# Terminal 2: Run organization tests
python backend/api/test_auth_endpoints.py
```

**Test Admin API (requires authentication):**
```bash
# Terminal 1: Start API server
python -m uvicorn backend.main:app --reload

# Terminal 2: Run admin tests
python backend/api/test_admin_api.py
```

## 📚 What's Been Built

### ✅ Organization Platform Features
- Multi-tenant architecture with organization isolation
- JWT-based authentication with organization context
- Email verification with OTP (6-digit codes, 10-minute expiration)
- Email-based member invitations (7-day expiration)
- Role-based access control (Owner, Admin, Member)
- Organization name uniqueness validation
- Multi-organization membership support

### ✅ Core RAG Pipeline
- Document loaders (PDF, DOCX, TXT)
- Text chunking (3 strategies: fixed, sentence, semantic)
- Embedding model (multilingual, Tamil-optimized)
- FAISS vector store with organization scoping
- Tamil-optimized prompts

### ✅ API Endpoints
- **Authentication**: Register, login, logout, email verification
- **Organizations**: Create, update, list, switch context
- **Members**: Invite, accept, remove, update roles
- **Documents**: Upload, ingest, list, delete (organization-scoped)
- **Chat**: Conversational AI with RAG (organization-scoped)
- **Admin**: Statistics, settings, user management

## 🎓 Next Steps

1. **Create your organization:**
   - Register at http://localhost:3000/register
   - Verify your email (if enabled)
   - Create your first organization
   - Invite team members

2. **Upload documents:**
   - Navigate to Admin → Upload
   - Upload PDFs, DOCX, or TXT files
   - Documents are automatically ingested and indexed
   - All documents are scoped to your organization

3. **Start chatting:**
   - Use the chat interface to ask questions
   - The AI will use your organization's documents as context
   - Try Tamil, English, or code-mixed queries

4. **Explore the API:**
   - Visit http://localhost:8000/docs for interactive API documentation
   - Test endpoints with your JWT token
   - Build custom integrations

## 🔧 Troubleshooting

**Organization setup issues:**
```bash
# Check if organization platform is enabled
grep ENABLE_ORGANIZATION_PLATFORM .env

# Verify database migrations
alembic current
alembic upgrade head
```

**Email not sending:**
```bash
# Check SMTP configuration in .env
grep SMTP_ .env

# Test email configuration
python -c "from backend.settings import settings; print(settings.SMTP_SERVER)"
```

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

- **docs/features/organization-management.md** - Organization platform details
- **docs/features/email-verification.md** - Email verification system
- **docs/features/member-management.md** - Member invitation and roles
- **docs/setup/email-configuration.md** - Email service setup guide
- **docs/project/ui-ux-design-specification.md** - UI/UX design guide
- **docs/api/organization-api.md** - Organization API reference
- **CLAUDE.md** - Detailed project documentation

## 🚧 Coming Next

- **Voice Interface**: Real-time voice assistant with STT/TTS
- **Advanced Analytics**: Usage statistics and insights
- **Document Management**: Version control and collaboration
- **API Integrations**: Webhooks and third-party integrations
- **Mobile App**: React Native mobile application

## 💡 Tips

- **Organization Isolation**: All data is strictly isolated by organization
- **Multi-Organization**: Users can belong to multiple organizations
- **Email Verification**: Enable for production to prevent spam
- **Unique Names**: Organization names must be globally unique
- **Role Hierarchy**: Owner > Admin > Member permissions
- **Document Scoping**: Documents are only accessible within their organization
- **Session Management**: JWT tokens include organization context

---

**Questions?** Check the documentation in the `docs/` directory or visit http://localhost:8000/docs for API documentation!
