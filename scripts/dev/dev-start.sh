#!/bin/bash

# Tamil AI Voice Assistant - Development Environment Startup Script
# This script sets up and starts the complete development environment

set -e  # Exit on any error

echo "🚀 Tamil AI Voice Assistant - Development Environment Setup"
echo "==========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Use docker compose if available, otherwise fall back to docker-compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

print_status "Using: $DOCKER_COMPOSE_CMD"

# Check for required directories
print_status "Creating required directories..."
mkdir -p data/{docs,faiss,chunks,logs,out}
mkdir -p credentials
mkdir -p migrations
mkdir -p models/llm

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"
        print_warning "Please review and update the .env file with your configuration"
    else
        print_warning "No .env.example found. Creating basic .env file..."
        cat > .env << 'EOF'
# Database Configuration
POSTGRES_PASSWORD=tamil_password_dev
DATABASE_URL=postgresql+asyncpg://tamil_user:tamil_password_dev@localhost:5432/tamil_assistant

# MinIO Configuration
MINIO_ROOT_USER=tamil_admin
MINIO_ROOT_PASSWORD=tamil_minio_password_dev

# Redis Configuration
REDIS_PASSWORD=tamil_redis_password_dev

# JWT Configuration (Change in production!)
JWT_SECRET_KEY=tamil_jwt_secret_dev_change_in_production_please

# LLM Configuration
USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://localhost:11435

# TTS Configuration
TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe
TTS_SPEAKING_RATE=1.10

# Other settings from existing configuration...
EOF
        print_success "Created basic .env file"
    fi
fi

# Check if Google Cloud credentials exist (for TTS)
if [ ! -f credentials/service-account-key.json ]; then
    print_warning "Google Cloud TTS credentials not found at credentials/service-account-key.json"
    print_warning "TTS will fall back to gTTS if Google Cloud credentials are not provided"
fi

# Function to wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml ps $service_name | grep -q "healthy"; then
            print_success "$service_name is healthy!"
            return 0
        fi

        if [ $attempt -eq 1 ]; then
            echo -n "Checking"
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo ""
    print_error "$service_name failed to become healthy within $(($max_attempts * 2)) seconds"
    return 1
}

# Stop any existing containers
print_status "Stopping any existing containers..."
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml down

# Pull latest images
print_status "Pulling latest images..."
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml pull

# Start infrastructure services first
print_status "Starting infrastructure services (PostgreSQL, Redis, MinIO)..."
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml up -d postgres redis minio

# Wait for infrastructure to be healthy
wait_for_service postgres
wait_for_service redis
wait_for_service minio

# Start Ollama
print_status "Starting Ollama LLM service..."
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml up -d ollama
wait_for_service ollama

# Start backend
print_status "Starting backend service..."
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml up -d backend

# Start frontend
print_status "Starting frontend service..."
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml up -d frontend

# Wait a bit for backend to start
print_status "Waiting for services to initialize..."
sleep 10

# Check if all services are running
print_status "Checking service status..."
if $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml ps | grep -q "Up"; then
    print_success "All services are running!"
else
    print_error "Some services may not be running properly"
fi

# Display service information
echo ""
echo "🎉 Development environment is ready!"
echo "=================================="
echo ""
echo "📊 Service Status:"
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml ps
echo ""

echo "🌐 Access Points:"
echo "  • Frontend (Next.js):     http://localhost:3000"
echo "  • Backend API:            http://localhost:8000"
echo "  • API Documentation:      http://localhost:8000/docs"
echo "  • MinIO Console:          http://localhost:9001"
echo "  • PostgreSQL:             localhost:5432 (user: tamil_user, db: tamil_assistant)"
echo "  • Redis:                  localhost:6379"
echo "  • Ollama:                 http://localhost:11435"
echo ""

echo "🔧 Useful Commands:"
echo "  • View logs:              $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml logs -f [service]"
echo "  • Stop services:          $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml down"
echo "  • Restart service:        $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml restart [service]"
echo "  • Execute in container:   $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml exec [service] bash"
echo ""

echo "📝 Next Steps:"
echo "  1. Check that all services are healthy: $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml ps"
echo "  2. Access the frontend at http://localhost:3000"
echo "  3. Check backend health at http://localhost:8000/health"
echo "  4. Review .env file configuration"
echo ""

print_warning "Note: First startup may take longer as Docker images are downloaded and built"
print_warning "If you encounter issues, check logs with: $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml logs"

echo ""
print_success "Development environment setup complete! 🎉"