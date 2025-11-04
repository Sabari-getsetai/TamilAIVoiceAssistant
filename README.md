# Tamil AI Voice Assistant

> A fully offline, privacy-focused conversational AI assistant designed specifically for Tamil language interactions. Features real-time voice conversations, document intelligence, and a complete admin dashboard.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/next.js-15+-black.svg)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

---

## 🎯 **What is Tamil AI Voice Assistant?**

The Tamil AI Voice Assistant is a **conversational AI system** that works like a live phone call in Tamil. It combines:

- 🗣️ **Natural Voice Conversations** - Speak naturally in Tamil, get intelligent responses
- 📄 **Document Intelligence** - Upload PDFs/documents and ask questions about them
- 🔒 **Complete Privacy** - 100% offline operation, your data never leaves your device
- 👨‍💼 **Admin Dashboard** - Manage documents, users, and system settings
- 🏗️ **Production Ready** - Multi-user architecture with authentication system

### **Key Features**
- ✅ **Real-time voice conversations** in Tamil with natural TTS
- ✅ **RAG-based document QA** - Upload and query documents intelligently
- ✅ **Multi-user support** with organizations and teams
- ✅ **Progressive Web App** - Install like a native app
- ✅ **Fully offline** - No internet required for core functionality
- ✅ **WebSocket-based** real-time communication
- ✅ **Admin dashboard** for document and user management

---

## 🚀 **Quick Start**

### **Option 1: One-Command Setup (Recommended)**
```bash
git clone <repository-url>
cd TamilAIVoiceAssistant
./scripts/dev/dev-start.sh
```

### **Option 2: Manual Setup**
```bash
# 1. Clone repository
git clone <repository-url>
cd TamilAIVoiceAssistant

# 2. Start services
docker compose -f docker-compose.dev.yml up -d

# 3. Install dependencies
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt

# 4. Install frontend dependencies
cd app/nextjs
npm install && npm run dev
```

### **After Setup**
- 🎨 **Frontend**: http://localhost:3000
- 🔗 **Backend API**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs
- 🗄️ **MinIO Console**: http://localhost:9001

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────┐
│ Tamil AI Voice Assistant - Architecture         │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Frontend     │  │ Backend      │            │
│  │ (Next.js)    │→ │ (FastAPI)    │            │
│  │ Port 3000    │  │ Port 8000    │            │
│  └──────────────┘  └────────┬─────┘            │
│                             │                   │
│  ┌──────────────┐  ┌────────▼─────┐            │
│  │ PostgreSQL   │  │ Redis Cache  │            │
│  │ + pgVector   │  │ + Sessions   │            │
│  │ Port 5432    │  │ Port 6379    │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ MinIO        │  │ Ollama       │            │
│  │ Storage      │  │ LLM Server   │            │
│  │ Port 9000    │  │ Port 11435   │            │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘
```

### **Technology Stack**
- **Frontend**: Next.js 15 + TypeScript + Material-UI
- **Backend**: FastAPI + Python 3.10+
- **Database**: PostgreSQL 16 + pgVector for vector similarity
- **Cache**: Redis for sessions and rate limiting
- **Storage**: MinIO for file management
- **AI**: LangChain + LangGraph for workflow orchestration
- **LLM**: Dual-mode (Ollama local + HuggingFace API)
- **Speech**: Faster-Whisper (STT) + Google Cloud TTS (Tamil)
- **Vector Search**: pgVector with 384-dimensional embeddings

---

## ✨ **Features & Capabilities**

### **🎤 Voice Interface**
- **Real-time conversations** in Tamil using WebSocket
- **Natural TTS** with Google Cloud Chirp3 HD voices
- **Voice Activity Detection** for seamless interaction
- **Noise reduction** for clear audio processing
- **Continuous conversation** flow like a phone call

### **📄 Document Intelligence**
- **Upload multiple formats** (PDF, DOCX, TXT)
- **RAG-powered QA** - Ask questions about your documents
- **Vector similarity search** with pgVector
- **Document management** with admin dashboard
- **Multi-user document isolation**

### **👥 User Management**
- **Multi-user authentication** with JWT
- **Organization support** for teams
- **Role-based access** (users, admins, org admins)
- **Anonymous mode** for testing and demos
- **Session management** with Redis caching

### **🎛️ Admin Dashboard**
- **Document management** - Upload, view, delete documents
- **User management** - Manage users and organizations
- **System statistics** - Monitor usage and performance
- **Configuration** - Adjust system settings
- **Real-time monitoring** of conversations

---

## 📚 **Documentation**

### **🎯 Getting Started**
- 📖 [**Getting Started Guide**](docs/getting-started/README.md) - New developer onboarding
- ⚡ [**Quick Setup**](docs/getting-started/quickstart.md) - Fast track setup
- 🔧 [**First Run Guide**](docs/getting-started/first-run.md) - Initial configuration

### **⚙️ Installation & Setup**
- 🐳 [**Docker Setup**](docs/setup/docker-setup.md) - Complete Docker environment
- 💻 [**Local Development**](docs/setup/local-development.md) - Native development setup
- 🤖 [**LLM Configuration**](docs/setup/llm-configuration.md) - Language model setup
- 🎤 [**Speech Setup**](docs/setup/speech-setup.md) - STT/TTS configuration

### **🏗️ Architecture & Development**
- 🏛️ [**Architecture Overview**](docs/architecture/README.md) - System design
- 📡 [**API Documentation**](docs/api/README.md) - Complete API reference
- 🛠️ [**Development Guide**](docs/development/README.md) - Development practices
- 🧪 [**Testing Guide**](docs/development/testing-guide.md) - Testing practices

### **✨ Features & Capabilities**
- 🗣️ [**Voice Assistant**](docs/features/voice-assistant.md) - Voice interface details
- 📄 [**Document Management**](docs/features/document-management.md) - RAG and documents
- 🔐 [**Authentication**](docs/features/user-authentication.md) - User management
- 👨‍💼 [**Admin Dashboard**](docs/features/admin-dashboard.md) - Administration

### **🆘 Support & Troubleshooting**
- 🔧 [**Common Issues**](docs/troubleshooting/common-issues.md) - Frequent problems
- 🐛 [**Installation Issues**](docs/troubleshooting/installation-issues.md) - Setup problems
- ❓ [**FAQ**](docs/troubleshooting/faq.md) - Frequently asked questions

> 📖 **[Complete Documentation Hub](docs/README.md)** - Comprehensive wiki-style documentation

---

## 🛠️ **Development**

### **Development Workflow**
```bash
# Start development environment
./scripts/dev/dev-start.sh

# Run tests
python tests/integration/test-infrastructure.py

# Check service health
docker compose -f docker-compose.dev.yml ps

# View logs
docker compose -f docker-compose.dev.yml logs -f [service]
```

### **Project Structure**
```
TamilAIVoiceAssistant/
├── 📁 app/nextjs/          # Next.js frontend (primary)
├── 📁 backend/             # FastAPI backend
│   ├── api/                # API endpoints
│   ├── database/           # Database models & connection
│   ├── cache/              # Redis integration
│   ├── storage/            # MinIO integration
│   ├── rag/                # RAG pipeline
│   ├── speech/             # STT/TTS processing
│   └── graphs/             # LangGraph workflows
├── 📁 docs/                # Wiki-style documentation
├── 📁 scripts/             # Utility scripts
├── 📁 tests/               # Test suites
├── 📁 data/                # Runtime data
├── 📁 models/              # AI models
└── 📁 migrations/          # Database migrations
```

### **Contributing**
1. **Fork the repository** and create a feature branch
2. **Follow our [coding standards](docs/development/coding-standards.md)**
3. **Add tests** for new functionality
4. **Update documentation** for changes
5. **Submit a pull request** with clear description

---

## 🧪 **Testing**

### **Run Test Suite**
```bash
# Infrastructure tests
python tests/integration/test-infrastructure.py

# RAG pipeline tests
python tests/utils/demo-rag-qa.py

# Audio processing tests
python tests/utils/test-noise-reduction.py

# Setup verification
python scripts/utils/verify-setup.py
```

### **Test Coverage**
- ✅ **Infrastructure tests** - Database, Redis, MinIO connectivity
- ✅ **API tests** - All endpoint functionality
- ✅ **Integration tests** - End-to-end workflows
- ✅ **Performance tests** - Response times and load testing
- ✅ **Audio tests** - STT/TTS processing validation

---

## 🔧 **Configuration**

### **Environment Configuration**
Copy `.env.example` to `.env` and configure:

```bash
# LLM Backend
USE_LOCAL_LLM=true  # true=Ollama, false=HuggingFace

# Database
DATABASE_URL=postgresql+asyncpg://tamil_user:password@localhost:5432/tamil_assistant

# Speech Services
TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe  # Premium Tamil voice
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
```

> 📋 **[Complete Configuration Reference](docs/reference/configuration-reference.md)**

---

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Start production services
docker compose -f docker-compose.prod.yml up -d

# Run database migrations
docker compose exec backend alembic upgrade head
```

### **Deployment Options**
- 🐳 **Docker Compose** - Single server deployment
- ☸️ **Kubernetes** - Scalable container orchestration
- ☁️ **Cloud Platforms** - AWS, GCP, Azure deployment guides
- 🖥️ **Local Deployment** - On-premises installation

> 🚀 **[Deployment Guide](docs/development/deployment.md)**

---

## 📊 **Project Status**

### **Current Version: v2.0 (January 2025)**

#### **✅ Completed Features**
- 🏗️ **Infrastructure** - PostgreSQL, Redis, MinIO, Docker setup
- 🎤 **Voice Interface** - Real-time Tamil conversations
- 📄 **Document RAG** - Upload and query documents
- 👨‍💼 **Admin Dashboard** - Complete document management
- 🔐 **User Authentication** - Multi-user with JWT
- 📱 **PWA Support** - Progressive web app features

#### **🔄 In Development**
- 👥 **Team Features** - Enhanced organization management
- 📊 **Analytics Dashboard** - Usage statistics and insights
- 🌍 **Multi-language** - Additional language support
- 🔊 **Voice Customization** - User voice preferences

#### **📅 Roadmap**
- 🤖 **Advanced AI** - Custom fine-tuned models
- 📱 **Mobile Apps** - Native iOS/Android applications
- 🔌 **API Integrations** - Third-party service integrations
- ☁️ **Cloud Deployment** - One-click cloud deployment

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 **Community**

### **Contributing**
We welcome contributions! Please read our [Contributing Guide](docs/development/contributing.md) for details on our code of conduct and the process for submitting pull requests.

### **Support**
- 📖 [Documentation](docs/README.md)
- 🐛 [Issue Tracker](../../issues)
- 💬 [Discussions](../../discussions)
- 📧 [Contact](mailto:support@example.com)

---

## 🙏 **Acknowledgments**

- **Tamil Language Community** - For inspiration and feedback
- **Open Source Projects** - FastAPI, Next.js, LangChain, and many others
- **Contributors** - Everyone who has contributed code, documentation, and ideas

---

**🎉 Ready to get started? Follow our [Quick Start Guide](docs/getting-started/quickstart.md) and join the Tamil AI revolution!**

*Built with ❤️ for the Tamil-speaking community*