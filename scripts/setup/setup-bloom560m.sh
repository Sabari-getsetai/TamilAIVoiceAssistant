#!/bin/bash
# Setup bloom-560m model in Ollama
# Usage: ./setup_bloom560m.sh

set -e

echo "=========================================="
echo "Setting up bloom-560m in Ollama"
echo "=========================================="

# Check if model file exists
if [ ! -f "models/llm/bloom-560m.q8_0.gguf" ]; then
    echo "❌ Error: bloom-560m.q8_0.gguf not found in models/llm/"
    echo ""
    echo "Please place your bloom-560m.q8_0.gguf file in models/llm/ directory first."
    echo "You can download it from HuggingFace or other sources."
    exit 1
fi

echo "✅ Found bloom-560m.q8_0.gguf"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "Starting Ollama container..."
docker compose -f docker-compose.dev.yml up -d

echo "Waiting for Ollama to be ready..."
sleep 5

# Create Modelfile
echo ""
echo "Creating Modelfile for bloom-560m..."
cat > models/llm/Modelfile << 'EOF'
FROM /models/bloom-560m.q8_0.gguf

PARAMETER temperature 0.7
PARAMETER num_ctx 2048
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM """You are a helpful multilingual AI assistant. You can understand and respond in multiple languages including Tamil and English."""
EOF

echo "✅ Modelfile created"

# Create model in Ollama
echo ""
echo "Creating bloom-560m model in Ollama (this may take a moment)..."
docker exec tamil-assistant-ollama ollama create bloom-560m -f /models/Modelfile

echo ""
echo "✅ bloom-560m model created successfully!"
echo ""

# Test the model
echo "Testing bloom-560m model..."
echo ""
docker exec tamil-assistant-ollama ollama run bloom-560m "Hello! Can you introduce yourself?"

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "You can now:"
echo "  1. Run the demo: python demo_rag_qa.py"
echo "  2. Query: python query_rag.py 'your question'"
echo "  3. Test Ollama: docker exec tamil-assistant-ollama ollama run bloom-560m 'test'"
echo ""
