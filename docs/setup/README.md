# Setup & Installation Guide

This section contains comprehensive installation and configuration guides for all components of the Tamil AI Voice Assistant.

## 🚀 **Quick Setup Options**

### **Option 1: Docker Development (Recommended)**
Complete containerized setup with all services:
- [🐳 **Docker Setup Guide**](docker-setup.md) - Full Docker development environment

### **Option 2: Local Development**
Native installation for development:
- [💻 **Local Development Setup**](local-development.md) - Native Python/Node.js setup

### **Option 3: Hybrid Setup**
Mix of local and containerized services:
- Combine guides based on your preference

---

## 📋 **Component-Specific Setup**

### **Core Infrastructure**
| Component | Guide | Purpose |
|-----------|-------|---------|
| 🐳 **Docker Environment** | [Docker Setup](docker-setup.md) | Complete containerized development |
| 💻 **Local Development** | [Local Setup](local-development.md) | Native development environment |
| 🧪 **Testing Environment** | [Testing Setup](testing-setup.md) | Test configuration and execution |
| 🎯 **IDE Configuration** | [IDE Setup](ide-configuration.md) | VS Code and development tools |

### **AI & Language Models**
| Component | Guide | Purpose |
|-----------|-------|---------|
| 🤖 **LLM Configuration** | [LLM Setup](llm-configuration.md) | Ollama + HuggingFace setup |
| 🎭 **Bloom Model** | [Bloom Setup](bloom-model-setup.md) | Specific Bloom model configuration |
| 🤗 **HuggingFace** | [HuggingFace Setup](huggingface-setup.md) | HuggingFace API integration |
| 💬 **Chat Completions** | [Chat API Setup](huggingface-chat-completions.md) | HuggingFace Chat API |

### **Speech & Audio**
| Component | Guide | Purpose |
|-----------|-------|---------|
| 🎤 **Speech Components** | [Speech Setup](speech-setup.md) | STT/TTS configuration |
| ☁️ **Google Cloud TTS** | [Google TTS Setup](google-cloud-tts.md) | Premium voice synthesis |
| 👩 **Female Voice** | [Female Voice Setup](female-voice-setup.md) | Female voice configuration |

---

## 🔧 **Installation Order**

### **Recommended Installation Sequence**

#### **Phase 1: Foundation**
1. 📋 **Prerequisites** - Install Docker, Python, Node.js
2. 🐳 **Docker Environment** - Set up containerized services
3. 🔧 **Basic Configuration** - Environment variables and settings

#### **Phase 2: Core Services**
1. 🗄️ **Database** - PostgreSQL with pgVector
2. 💾 **Cache** - Redis for sessions
3. 📁 **Storage** - MinIO for files
4. 🤖 **LLM** - Ollama or HuggingFace

#### **Phase 3: AI Components**
1. 🎤 **Speech Processing** - STT/TTS setup
2. ☁️ **Cloud Services** - Google Cloud TTS (optional)
3. 📄 **Document Processing** - RAG pipeline
4. 🔍 **Vector Search** - Embeddings and similarity

#### **Phase 4: Development Tools**
1. 🎯 **IDE Setup** - VS Code configuration
2. 🧪 **Testing** - Test environment setup
3. 🐛 **Debugging** - Development tools
4. ✅ **Validation** - Full system test

---

## 🛠️ **Setup Guides by Role**

### **For New Developers**
Start here if you're new to the project:
1. [🐳 Docker Setup](docker-setup.md) - Easiest way to get started
2. [🎯 IDE Configuration](ide-configuration.md) - Development environment
3. [🧪 Testing Setup](testing-setup.md) - Validate your installation

### **For AI/ML Engineers**
Focus on the AI components:
1. [🤖 LLM Configuration](llm-configuration.md) - Language models
2. [🎤 Speech Setup](speech-setup.md) - Audio processing
3. [🤗 HuggingFace Setup](huggingface-setup.md) - Model APIs
4. [🎭 Bloom Model](bloom-model-setup.md) - Specific model setup

### **For Frontend Developers**
Frontend-focused setup:
1. [💻 Local Development](local-development.md) - Node.js and Next.js
2. [🎯 IDE Configuration](ide-configuration.md) - VS Code for React/TS
3. [🧪 Testing Setup](testing-setup.md) - Frontend testing

### **For Backend Developers**
Backend-focused setup:
1. [🐳 Docker Setup](docker-setup.md) - Database and services
2. [💻 Local Development](local-development.md) - Python environment
3. [🤖 LLM Configuration](llm-configuration.md) - AI integration

### **For DevOps Engineers**
Infrastructure-focused setup:
1. [🐳 Docker Setup](docker-setup.md) - Container orchestration
2. [☁️ Google Cloud TTS](google-cloud-tts.md) - Cloud integration
3. [🧪 Testing Setup](testing-setup.md) - Infrastructure validation

---

## 📱 **Platform-Specific Instructions**

### **Linux (Ubuntu/Debian)**
```bash
# Install Docker
sudo apt update && sudo apt install docker.io docker-compose-plugin

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### **macOS**
```bash
# Install via Homebrew
brew install docker docker-compose python@3.10 node

# Start Docker Desktop
open -a Docker
```

### **Windows**
```powershell
# Install via Chocolatey
choco install docker-desktop python nodejs

# Or use Windows Subsystem for Linux (WSL2)
wsl --install
```

---

## 🔧 **Configuration Templates**

### **Environment Configuration**
All setup guides use these configuration files:
- 📄 **`.env`** - Environment variables (created from `.env.example`)
- 🐳 **`docker-compose.dev.yml`** - Docker services configuration
- ⚙️ **`alembic.ini`** - Database migration configuration

### **Quick Configuration Check**
```bash
# Verify configuration files exist
ls -la .env docker-compose.dev.yml alembic.ini

# Check Docker services
docker compose -f docker-compose.dev.yml config

# Validate environment
python scripts/utils/verify-setup.py
```

---

## 🧪 **Validation & Testing**

### **Post-Setup Validation**
After completing any setup guide:

```bash
# 1. Run infrastructure tests
python tests/integration/test-infrastructure.py

# 2. Check service health
./scripts/dev/check-services.sh

# 3. Verify API endpoints
curl http://localhost:8000/health

# 4. Test frontend
curl http://localhost:3000
```

### **Common Validation Commands**
```bash
# Check Docker containers
docker compose -f docker-compose.dev.yml ps

# View service logs
docker compose -f docker-compose.dev.yml logs -f [service]

# Test database connection
python -c "from backend.database.connection import check_db_health; import asyncio; print(asyncio.run(check_db_health()))"

# Test Redis connection
python -c "from backend.cache.redis_client import check_redis_health; import asyncio; print(asyncio.run(check_redis_health()))"
```

---

## 🆘 **Troubleshooting Setup Issues**

### **Common Setup Problems**
- 🐳 **Docker Issues** - [Docker Troubleshooting](../troubleshooting/installation-issues.md#docker-issues)
- 🐍 **Python Issues** - [Python Environment](../troubleshooting/installation-issues.md#python-issues)
- 📦 **Node.js Issues** - [Node.js Problems](../troubleshooting/installation-issues.md#nodejs-issues)
- 🔧 **Configuration Issues** - [Config Problems](../troubleshooting/installation-issues.md#configuration-issues)

### **Quick Fixes**
```bash
# Reset Docker environment
docker compose -f docker-compose.dev.yml down -v
docker system prune -f

# Reset Python environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Reset Node.js environment
rm -rf app/nextjs/node_modules
cd app/nextjs && npm install
```

---

## 📚 **Additional Resources**

### **Related Documentation**
- 🏗️ [Architecture Overview](../architecture/README.md) - Understand the system design
- 🎯 [Getting Started](../getting-started/README.md) - New developer onboarding
- 🛠️ [Development Guide](../development/README.md) - Development workflows
- 🆘 [Troubleshooting](../troubleshooting/README.md) - Problem solving

### **External Resources**
- 🐳 [Docker Documentation](https://docs.docker.com/)
- 🐍 [Python Installation Guide](https://www.python.org/downloads/)
- 📦 [Node.js Installation](https://nodejs.org/en/download/)
- ⚛️ [Next.js Documentation](https://nextjs.org/docs)
- 🤗 [HuggingFace Documentation](https://huggingface.co/docs)

---

*Ready to start? Pick the setup guide that matches your needs and follow the step-by-step instructions!*