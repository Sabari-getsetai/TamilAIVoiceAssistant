# Getting Started with Tamil AI Voice Assistant

Welcome to the Tamil AI Voice Assistant! This guide will help you get up and running quickly, whether you're a new developer joining the project or an experienced developer wanting to contribute.

## 🚀 **Quick Start**

### **Option 1: Fast Track (Recommended)**
```bash
# Clone and start in 3 commands
git clone <repository-url>
cd TamilAIVoiceAssistant
./scripts/dev/dev-start.sh
```

### **Option 2: Manual Setup**
If you prefer step-by-step control, follow our [Complete Setup Guide](../setup/README.md).

---

## 📋 **Prerequisites**

Before you begin, ensure you have:

- **Docker & Docker Compose** - For containerized development
- **Python 3.10+** - For backend development
- **Node.js 18+** - For frontend development
- **Git** - For version control
- **4GB+ RAM** - For running all services

**Detailed requirements**: [Prerequisites Guide](prerequisites.md)

---

## 🎯 **What You'll Have After Setup**

### **Running Services**
- 🎨 **Frontend**: http://localhost:3000 (Next.js with Material-UI)
- 🔗 **Backend API**: http://localhost:8000 (FastAPI with live docs)
- 🗄️ **Database**: PostgreSQL with pgVector for embeddings
- 💾 **Cache**: Redis for session management
- 📁 **Storage**: MinIO for file management
- 🤖 **LLM**: Ollama for local language model inference

### **Key Features Working**
- ✅ Voice conversation in Tamil
- ✅ Document upload and RAG question answering
- ✅ Real-time WebSocket communication
- ✅ Admin dashboard for document management
- ✅ Multi-user architecture (ready for authentication)

---

## 📖 **Step-by-Step Guides**

### **1. First-Time Setup**
- [📋 Prerequisites](prerequisites.md) - System requirements and dependencies
- [⚡ Quick Setup](quickstart.md) - Fast track to running system
- [🔧 First Run](first-run.md) - Initial configuration and validation

### **2. Development Workflow**
- [💻 Development Workflow](development-workflow.md) - Daily development tasks
- [🐛 Debugging Guide](../development/debugging.md) - Troubleshooting common issues
- [🧪 Testing Guide](../development/testing-guide.md) - Running and writing tests

### **3. Understanding the System**
- [🏗️ Architecture Overview](../architecture/README.md) - High-level system design
- [✨ Feature Overview](../features/README.md) - What the system can do
- [📡 API Overview](../api/README.md) - Available endpoints and usage

---

## 🛠️ **Development Environment**

### **Recommended IDE Setup**
- **VS Code** with our [recommended extensions](../setup/ide-configuration.md)
- **Python language server** for backend development
- **TypeScript support** for frontend development
- **Docker extension** for container management

### **Development Commands**
```bash
# Start development environment
./scripts/dev/dev-start.sh

# Run tests
python tests/utils/test-infrastructure.py

# Check service health
./scripts/dev/check-services.sh

# View logs
docker compose -f docker-compose.dev.yml logs -f [service]
```

---

## 🎯 **Learning Path**

### **For Backend Developers**
1. 📖 [Backend Architecture](../architecture/backend-architecture.md)
2. 🔗 [API Documentation](../api/README.md)
3. 🗄️ [Database Schema](../architecture/database-design.md)
4. 🧪 [Testing Backend](../development/testing-guide.md)

### **For Frontend Developers**
1. 🎨 [Frontend Architecture](../architecture/frontend-architecture.md)
2. ⚛️ [Next.js Setup](../setup/ide-configuration.md)
3. 🎤 [Voice Interface](../features/voice-assistant.md)
4. 📱 [UI Components](../features/admin-dashboard.md)

### **For DevOps/Infrastructure**
1. 🐳 [Docker Setup](../setup/docker-setup.md)
2. 🗄️ [Database Setup](../architecture/database-design.md)
3. ☁️ [Cloud Services](../setup/google-cloud-tts.md)
4. 🚀 [Deployment](../development/deployment.md)

### **For AI/ML Developers**
1. 🤖 [LLM Configuration](../setup/llm-configuration.md)
2. 📄 [RAG Pipeline](../features/conversation-pipeline.md)
3. 🎙️ [Speech Processing](../setup/speech-setup.md)
4. 🔍 [Model Information](../reference/models-info.md)

---

## 🤝 **Contributing**

Ready to contribute? Great! Here's how:

1. **Setup Development Environment** - Follow the quick start above
2. **Read Contributing Guidelines** - [Contributing Guide](../development/contributing.md)
3. **Pick an Issue** - Check our [task tracking](../project/tasks.md)
4. **Follow Coding Standards** - [Coding Standards](../development/coding-standards.md)

### **First Contribution Ideas**
- 📝 Improve documentation
- 🐛 Fix small bugs
- 🧪 Add test coverage
- 🌍 Improve Tamil language support
- ✨ Enhance UI components

---

## 🆘 **Need Help?**

### **Common Issues**
- 🔧 [Installation Issues](../troubleshooting/installation-issues.md)
- 🏃 [Runtime Issues](../troubleshooting/runtime-issues.md)
- 🐛 [Common Problems](../troubleshooting/common-issues.md)
- ❓ [FAQ](../troubleshooting/faq.md)

### **Getting Support**
- 📖 Check our comprehensive [documentation](../README.md)
- 🔍 Search [troubleshooting guides](../troubleshooting/README.md)
- 📋 Review [common issues](../troubleshooting/common-issues.md)
- 💬 Ask questions in project discussions

---

## 🎉 **You're Ready!**

After completing the setup, you'll have a fully functional Tamil AI Voice Assistant running locally. The system includes:

- 🗣️ **Voice Interface** - Natural conversation in Tamil
- 📄 **Document Intelligence** - Upload and query documents
- 👨‍💼 **Admin Dashboard** - Manage documents and settings
- 🔗 **REST API** - Programmatic access to all features
- 🧪 **Test Suite** - Comprehensive testing infrastructure

**Next Steps**:
- 🎤 Try the [voice interface](http://localhost:3000/voice)
- 📊 Explore the [admin dashboard](http://localhost:3000/admin)
- 📡 Test the [API endpoints](http://localhost:8000/docs)
- 🧪 Run the [test suite](../development/testing-guide.md)

Welcome to the Tamil AI Voice Assistant development community! 🚀