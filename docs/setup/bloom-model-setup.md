# Bloom-560M Setup Guide

This guide helps you set up the **bloom-560m** model with Ollama for the Tamil AI Voice Assistant.

## Why bloom-560m?

- **Smaller size**: 560M parameters (~560MB in Q8 quantization)
- **Faster inference**: Much faster than 7B models
- **Lower memory**: Runs well on systems with 2-3GB RAM
- **Multilingual**: Supports 46+ languages including Tamil and English

## Prerequisites

1. **bloom-560m.q8_0.gguf file** - You need to have this file
2. **Docker** - For running Ollama
3. **Python environment** - Already set up

## Quick Setup (Automated)

If you already have `bloom-560m.q8_0.gguf` in `models/llm/` directory:

```bash
# Run the automated setup script
./setup_bloom560m.sh
```

This script will:
- ✅ Check if model file exists
- ✅ Start Ollama container
- ✅ Create Modelfile with optimal settings
- ✅ Import bloom-560m into Ollama
- ✅ Test the model

## Manual Setup

If you prefer manual setup or need to troubleshoot:

### Step 1: Place Model File

```bash
# Make sure your model file is in the correct location
ls -lh models/llm/bloom-560m.q8_0.gguf

# Should show: ~560MB file
```

### Step 2: Start Ollama

```bash
# Start Ollama Docker container
docker compose -f docker-compose.dev.yml up -d

# Verify Ollama is running
docker ps | grep ollama
```

### Step 3: Create Modelfile

```bash
# Create Modelfile for bloom-560m
cat > models/llm/Modelfile << 'EOF'
FROM /models/bloom-560m.q8_0.gguf

PARAMETER temperature 0.7
PARAMETER num_ctx 2048
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM """You are a helpful multilingual AI assistant. You can understand and respond in multiple languages including Tamil and English."""
EOF
```

**Modelfile Parameters Explained:**
- `temperature 0.7` - Balanced creativity (0=deterministic, 1=creative)
- `num_ctx 2048` - Context window size (lower = less memory)
- `top_p 0.9` - Nucleus sampling for better quality
- `top_k 40` - Limits vocabulary choices per token

### Step 4: Import Model into Ollama

```bash
# Create the model in Ollama
docker exec tamil-assistant-ollama ollama create bloom-560m -f /models/Modelfile

# This may take a moment...
```

### Step 5: Test the Model

```bash
# Test in English
docker exec tamil-assistant-ollama ollama run bloom-560m "Hello! Can you introduce yourself?"

# Test in Tamil
docker exec tamil-assistant-ollama ollama run bloom-560m "வணக்கம்! நீங்கள் யார்?"

# Exit: Ctrl+D or type /bye
```

## Running the Demo

Once bloom-560m is set up in Ollama:

```bash
# Run the complete RAG demo
python demo_rag_qa.py

# Or query directly
python query_rag.py "செயற்கை நுண்ணறிவு என்றால் என்ன?"

# Interactive mode
python query_rag.py
```

## Verification

Check if bloom-560m is available in Ollama:

```bash
# List all models in Ollama
docker exec tamil-assistant-ollama ollama list

# Should show:
# NAME            ID              SIZE    MODIFIED
# bloom-560m      ...             560MB   ...
```

## Troubleshooting

### Error: "bloom-560m.q8_0.gguf not found"

**Solution:** Place the model file in `models/llm/` directory:
```bash
# Check current location
ls models/llm/

# Copy from your download location (example)
cp ~/Downloads/bloom-560m.q8_0.gguf models/llm/
```

### Error: "Docker is not running"

**Solution:** Start Docker:
```bash
# Start Docker daemon
sudo systemctl start docker  # Linux
# or open Docker Desktop (Mac/Windows)
```

### Error: "Ollama container not found"

**Solution:** Start Ollama:
```bash
docker compose -f docker-compose.dev.yml up -d
```

### Error: "Model not responding" or "Slow inference"

**Solutions:**
1. **Reduce context window** - Edit Modelfile and change `num_ctx` to 1024 or 512
2. **Check system resources** - `docker stats` to see memory usage
3. **Restart Ollama** - `docker compose -f docker-compose.dev.yml restart`

### Model generates poor quality output

**Solutions:**
1. **Adjust temperature** - Lower for more factual (0.3-0.5), higher for creative (0.8-1.0)
2. **Increase top_k** - Try 60-80 for more diverse responses
3. **Check prompt** - Bloom works best with clear, structured prompts

## Model Information

**Bloom-560M Specifications:**
- **Parameters**: 560 million
- **Languages**: 46+ languages (including Tamil, English, French, Spanish, etc.)
- **Quantization**: Q8 (8-bit, good balance of quality and size)
- **Context Window**: 2048 tokens (configurable)
- **Memory Usage**: ~600MB-800MB RAM
- **Inference Speed**: Fast (depends on CPU)

**Bloom Family:**
- bloom-560m (this one) - Smallest, fastest
- bloom-1b1 - Medium size
- bloom-3b - Larger
- bloom-7b1 - Largest

## Comparison: bloom-560m vs tamil-llama-7b

| Aspect | bloom-560m | tamil-llama-7b |
|--------|------------|----------------|
| Size | 560MB | 3.9GB |
| Parameters | 560M | 7B |
| Memory Usage | ~800MB | ~4GB |
| Speed | Fast | Slower |
| Tamil Quality | Good | Excellent |
| Multilingual | 46+ languages | Primarily Tamil/English |
| Resource Requirements | Low | High |

**Recommendation:**
- Use **bloom-560m** for systems with limited RAM (2-3GB)
- Use **tamil-llama-7b** if you have 4GB+ RAM and need best Tamil quality

## Next Steps

After bloom-560m is working:
1. ✅ Test with Tamil queries: `python query_rag.py "Tamil question"`
2. ✅ Run full demo: `python demo_rag_qa.py`
3. ✅ Ingest your own documents via Admin API
4. 🔄 Continue with Phase 5: Speech Processing (STT, TTS, VAD)

## Additional Resources

- **Bloom Model Card**: https://huggingface.co/bigscience/bloom-560m
- **Ollama Documentation**: https://ollama.ai/docs
- **GGUF Format**: https://github.com/ggerganov/llama.cpp

---

**Need help?** Check CLAUDE.md or create an issue in the repository.
