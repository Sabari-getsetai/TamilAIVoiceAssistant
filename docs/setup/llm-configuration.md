# Dual-Mode LLM Setup Guide

## Overview

The Tamil AI Voice Assistant now supports **dual-mode LLM operation**, allowing seamless switching between:

1. **Local Mode**: Uses Ollama with locally running models (no internet required)
2. **Cloud Mode**: Uses HuggingFace Chat Completions API for advanced Tamil models

## Architecture

### Unified LLM Interface

The system provides a unified interface (`backend/models/__init__.py`) that automatically selects the appropriate backend based on configuration:

```python
from backend.models import get_llm, initialize_llm

# Get LLM instance (automatically selects backend)
llm = get_llm()

# Initialize the model
if initialize_llm():
    # Generate text
    response = llm.generate("Your prompt here")
```

### Backend Selection

Backend selection is controlled via the `.env` file:

```bash
# Use local Ollama models
USE_LOCAL_LLM=true

# Use HuggingFace cloud models
USE_LOCAL_LLM=false
```

## Local Mode Setup

### Prerequisites

1. Docker and Docker Compose installed
2. Sufficient disk space for models (~2-4GB per model)

### Quick Start

```bash
# 1. Start Ollama service
docker compose -f docker-compose.dev.yml up -d ollama

# 2. Pull a model (choose one)
docker exec tamil-assistant-ollama ollama pull tinyllama
docker exec tamil-assistant-ollama ollama pull sarvam-tamil-fast

# 3. Configure for local mode
echo "USE_LOCAL_LLM=true" >> .env

# 4. Test
python backend/models/__init__.py
```

### Available Local Models

- **tinyllama**: Fast, lightweight model (1.1B parameters)
- **sarvam-tamil-fast**: Optimized Tamil model (quantized)
- **sarvam-tamil**: Full Tamil model (better quality, slower)

### Benefits

✅ No internet required  
✅ No API costs  
✅ Full data privacy  
✅ Consistent performance  
✅ No rate limits

### Limitations

⚠️ Requires local resources (RAM/CPU)  
⚠️ Model quality depends on size  
⚠️ Initial download required

## Cloud Mode Setup

### Prerequisites

1. HuggingFace account (free)
2. Internet connection
3. API token

### Quick Start

```bash
# 1. Get HuggingFace API token
# Visit: https://huggingface.co/settings/tokens
# Create a new token with read permissions

# 2. Configure environment
cat >> .env << EOF
HF_API_TOKEN=your_token_here
USE_LOCAL_LLM=false
HF_MODEL_NAME=akdiwahar/KavithaSaaram-2b-it
EOF

# 3. Test
python backend/models/llm_huggingface.py
```

### Available Cloud Models

- **akdiwahar/KavithaSaaram-2b-it**: Tamil instruction-tuned model (2B parameters)
- **google/flan-t5-small**: Multilingual model
- **microsoft/DialoGPT-small**: Conversational model

### Benefits

✅ No local resources required  
✅ Access to latest models  
✅ Better quality for complex tasks  
✅ Automatic updates  
✅ Scalable

### Limitations

⚠️ Requires internet connection  
⚠️ API rate limits may apply  
⚠️ Potential latency  
⚠️ Data sent to external service

## HuggingFace Chat Completions API

### Implementation

The cloud mode uses HuggingFace's OpenAI-compatible chat completions endpoint:

```python
# Endpoint
https://router.huggingface.co/v1/chat/completions

# Request format
{
    "model": "akdiwahar/KavithaSaaram-2b-it",
    "messages": [
        {"role": "user", "content": "Your prompt"}
    ],
    "max_tokens": 512,
    "temperature": 0.7
}
```

### Features

- **Chat Format**: Better for conversational AI
- **System Prompts**: Support for context injection
- **Streaming**: Real-time response generation (future)
- **OpenAI Compatible**: Easy migration

### Example Usage

```python
from backend.models.llm_huggingface import HuggingFaceLLM

llm = HuggingFaceLLM(
    model_name="akdiwahar/KavithaSaaram-2b-it",
    api_token="your_token"
)

if llm.load_model():
    # Simple generation
    response = llm.generate("வணக்கம்!")
    
    # With system prompt
    response = llm.generate(
        prompt="Explain AI",
        system_prompt="You are a helpful Tamil assistant"
    )
```

## Switching Between Modes

### Runtime Switching

```python
from backend.models import get_llm

# Get current backend
llm = get_llm()
backend = llm.get_current_backend()
print(f"Using: {backend}")  # "local" or "huggingface"

# Get model info
info = llm.get_model_info()
print(info)
```

### Configuration

Edit `.env` file:

```bash
# Switch to local
USE_LOCAL_LLM=true

# Switch to cloud
USE_LOCAL_LLM=false
```

## RAG Integration

The dual-mode system integrates seamlessly with the RAG pipeline:

```python
from backend.models import get_llm, initialize_llm
from backend.rag import get_rag_prompt_builder

# Initialize LLM (auto-selects backend)
llm = get_llm()
initialize_llm()

# Build RAG prompt
prompt_builder = get_rag_prompt_builder()
rag_prompt = prompt_builder.build_with_context(
    question="செயற்கை நுண்ணறிவு என்றால் என்ன?",
    context_documents=retrieved_docs
)

# Generate answer (works with both backends)
answer = llm.generate(rag_prompt)
```

## Performance Comparison

### Local Mode (tinyllama)

- **Speed**: ~50-100 tokens/sec (CPU)
- **Quality**: Good for simple tasks
- **Latency**: <100ms
- **Cost**: Free (after download)

### Cloud Mode (KavithaSaaram-2b-it)

- **Speed**: Depends on API
- **Quality**: Better for Tamil
- **Latency**: 200-500ms
- **Cost**: Free tier available

## Best Practices

### When to Use Local Mode

- Development and testing
- Privacy-sensitive applications
- Offline environments
- High-volume requests
- Cost optimization

### When to Use Cloud Mode

- Production deployments
- Tamil-specific tasks
- Limited local resources
- Latest model access
- Scalability requirements

## Troubleshooting

### Local Mode Issues

```bash
# Check Ollama status
docker ps | grep ollama

# View Ollama logs
docker logs tamil-assistant-ollama

# List available models
docker exec tamil-assistant-ollama ollama list

# Pull model if missing
docker exec tamil-assistant-ollama ollama pull tinyllama
```

### Cloud Mode Issues

```bash
# Test API token
curl https://router.huggingface.co/v1/chat/completions \
    -H "Authorization: Bearer $HF_API_TOKEN" \
    -H 'Content-Type: application/json' \
    -d '{
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "akdiwahar/KavithaSaaram-2b-it"
    }'

# Check token validity
# Visit: https://huggingface.co/settings/tokens
```

### Common Errors

**Error**: "Model not loaded"
- **Solution**: Call `initialize_llm()` before `generate()`

**Error**: "Ollama connection failed"
- **Solution**: Start Ollama service with Docker Compose

**Error**: "Invalid credentials"
- **Solution**: Verify HF_API_TOKEN in .env file

**Error**: "Model not found"
- **Solution**: Pull model with `ollama pull <model_name>`

## Future Enhancements

- [ ] Streaming support for both backends
- [ ] Model caching and optimization
- [ ] Automatic fallback on failure
- [ ] Performance monitoring
- [ ] Cost tracking for cloud mode
- [ ] Multi-model ensemble
- [ ] Fine-tuning support

## References

- [Ollama Documentation](https://ollama.ai/docs)
- [HuggingFace Inference API](https://huggingface.co/docs/api-inference)
- [KavithaSaaram Model](https://huggingface.co/akdiwahar/KavithaSaaram-2b-it)
- [Project Documentation](../project/product-requirements.md)
