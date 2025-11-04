#!/bin/bash
# Quick Ollama Health Check Script

echo "================================================================================"
echo "🔍 Ollama Health Check"
echo "================================================================================"

# Check if Docker is running
echo ""
echo "1. Checking Docker..."
if docker ps &> /dev/null; then
    echo "   ✅ Docker is running"
else
    echo "   ❌ Docker is not running or not accessible"
    exit 1
fi

# Check if Ollama container is running
echo ""
echo "2. Checking Ollama container..."
if docker ps | grep -q tamil-assistant-ollama; then
    echo "   ✅ Ollama container is running"
else
    echo "   ❌ Ollama container is not running"
    echo "   Run: docker compose -f docker-compose.dev.yml up -d"
    exit 1
fi

# Check system memory
echo ""
echo "3. Checking system memory..."
free -h | grep "Mem:"
echo ""
AVAILABLE=$(free -m | awk 'NR==2 {print $7}')
if [ "$AVAILABLE" -lt 2000 ]; then
    echo "   ⚠️  Low available memory: ${AVAILABLE}MB"
    echo "   Consider closing other applications"
else
    echo "   ✅ Available memory: ${AVAILABLE}MB"
fi

# Check Ollama models
echo ""
echo "4. Checking installed models..."
docker exec tamil-assistant-ollama ollama list

# Test Ollama API
echo ""
echo "5. Testing Ollama API..."
RESPONSE=$(curl -s http://localhost:11435/api/tags)
if [ $? -eq 0 ]; then
    echo "   ✅ Ollama API is responding"
else
    echo "   ❌ Ollama API is not responding"
    exit 1
fi

# Test model loading
echo ""
echo "6. Testing model availability..."
# Check if llama3.2:1b exists
if docker exec tamil-assistant-ollama ollama list | grep -q "llama3.2:1b"; then
    echo "   ✅ llama3.2:1b is available (recommended for low memory)"
elif docker exec tamil-assistant-ollama ollama list | grep -q "llama2"; then
    echo "   ✅ llama2 is available (needs ~4GB memory)"
    echo "   💡 Consider installing llama3.2:1b for better performance:"
    echo "      docker exec tamil-assistant-ollama ollama pull llama3.2:1b"
else
    echo "   ⚠️  No models found!"
    echo "   Install a model with:"
    echo "      docker exec tamil-assistant-ollama ollama pull llama3.2:1b"
fi

# Test simple generation
echo ""
echo "7. Testing model generation..."
TEST_RESULT=$(curl -s http://localhost:11435/api/generate -d '{"model":"llama3.2:1b","prompt":"Hi","stream":false}' 2>&1)
if echo "$TEST_RESULT" | grep -q "error"; then
    ERROR_MSG=$(echo "$TEST_RESULT" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
    echo "   ❌ Generation test failed: $ERROR_MSG"
    if echo "$ERROR_MSG" | grep -q "memory"; then
        echo ""
        echo "   💡 Recommendations:"
        echo "      1. Install smaller model: docker exec tamil-assistant-ollama ollama pull llama3.2:1b"
        echo "      2. Close other applications to free memory"
        echo "      3. Restart Docker: docker compose -f docker-compose.dev.yml restart"
    fi
else
    echo "   ✅ Model generation working!"
fi

echo ""
echo "================================================================================"
echo "✅ Health check complete!"
echo "================================================================================"
