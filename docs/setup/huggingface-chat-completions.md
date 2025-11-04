# HuggingFace Chat Completions API Setup Guide

## Overview

This guide explains how to use HuggingFace's Chat Completions API with the Tamil AI Voice Assistant for cloud-based LLM inference.

## Key Findings

### ✅ What Works

The HuggingFace Chat Completions API (`https://router.huggingface.co/v1/chat/completions`) provides OpenAI-compatible chat completions for supported models.

**Working Implementation:**
```python
import os
import requests

API_URL = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

response = query({
    "messages": [
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ],
    "model": "meta-llama/Llama-3.2-3B-Instruct"
})

print(response["choices"][0]["message"])
```

### ⚠️ Model Availability

**Important:** Not all HuggingFace models are available through the Chat Completions router. The router only supports models from enabled providers.

**Tested Models:**

✅ **Working:**
- `meta-llama/Llama-3.2-3B-Instruct` - Excellent multilingual support including Tamil
- `meta-llama/Llama-3.2-1B-Instruct` - Smaller, faster variant

❌ **Not Supported:**
- `akdiwahar/KavithaSaaram-2b-it` - Tamil-specific model (not available via router)
- Most custom fine-tuned models

**Error when using unsupported model:**
```json
{
  "error": {
    "message": "The requested model 'akdiwahar/KavithaSaaram-2b-it' is not supported by any provider you have enabled.",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_supported"
  }
}
```

## Setup Instructions

### 1. Get HuggingFace API Token

1. Visit https://huggingface.co/settings/tokens
2. Create a new token with **read** permissions
3. Copy the token (starts with `hf_`)

### 2. Configure Environment

Create or update `.env` file:

```bash
# HuggingFace API Token
HF_TOKEN=hf_your_token_here

# Use cloud mode
USE_LOCAL_LLM=false

# Choose a supported model
HF_MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
```

**Important:** The environment variable must be named `HF_TOKEN`, not `HF_API_TOKEN`.

### 3. Update Settings

The `backend/settings.py` file should have:

```python
class Settings(BaseSettings):
    # ...
    HF_TOKEN: str = ""  # NOT HF_API_TOKEN
    HF_MODEL_NAME: str = "meta-llama/Llama-3.2-3B-Instruct"
    # ...
```

### 4. Test the Integration

```bash
# Test HuggingFace API directly
python backend/models/llm_huggingface.py

# Test unified interface
python backend/models/__init__.py
```

## Implementation Details

### Request Format

```python
{
    "messages": [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Your question here"}
    ],
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "max_tokens": 150,
    "temperature": 0.7
}
```

### Response Format

```python
{
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "The generated response text"
            },
            "finish_reason": "length"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 50,
        "total_tokens": 60
    }
}
```

### Error Handling

The implementation includes comprehensive error handling:

```python
try:
    response = requests.post(self.api_url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error Response: {response.text}")
        return None
        
    return response.json()
except Exception as e:
    print(f"Request Exception: {e}")
    return None
```

## Tamil Language Support

### Llama 3.2 Tamil Performance

The `meta-llama/Llama-3.2-3B-Instruct` model provides good Tamil language support:

**Example Tamil Query:**
```
வணக்கம்! செயற்கை நுண்ணறிவு என்றால் என்ன?
```

**Response:**
```
வணக்கம்! செயற்கை நுண்ணறிவு என்பது கண்டுபிடிக்கப்பட்ட கணினி ரோபோட்டிக்ஸ் மற்று...
```

The model can:
- ✅ Understand Tamil queries
- ✅ Generate Tamil responses
- ✅ Handle mixed Tamil-English content
- ✅ Maintain context in conversations

## Dual-Mode Operation

### Switching Between Local and Cloud

**Cloud Mode (HuggingFace):**
```bash
# .env
USE_LOCAL_LLM=false
HF_TOKEN=hf_your_token
HF_MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
```

**Local Mode (Ollama):**
```bash
# .env
USE_LOCAL_LLM=true
```

### Unified Interface

The system automatically selects the appropriate backend:

```python
from backend.models import get_llm, initialize_llm

# Automatically uses cloud or local based on USE_LOCAL_LLM
llm = get_llm()
initialize_llm()

# Generate text (works with both backends)
response = llm.generate("Your prompt here")
```

## Performance Comparison

### Cloud Mode (Llama-3.2-3B)

**Advantages:**
- ✅ Better quality responses
- ✅ Excellent multilingual support
- ✅ No local resources required
- ✅ Always up-to-date
- ✅ Scalable

**Limitations:**
- ⚠️ Requires internet connection
- ⚠️ API rate limits
- ⚠️ Latency (200-500ms)
- ⚠️ Data sent to external service

### Local Mode (Ollama)

**Advantages:**
- ✅ No internet required
- ✅ Full privacy
- ✅ No rate limits
- ✅ Low latency (<100ms)
- ✅ No API costs

**Limitations:**
- ⚠️ Requires local resources
- ⚠️ Model quality depends on size
- ⚠️ Initial download required

## Troubleshooting

### Common Issues

**1. Invalid Credentials Error**

```
Error: Invalid credentials in Authorization header
```

**Solution:**
- Verify `HF_TOKEN` is set correctly in `.env`
- Ensure token has read permissions
- Check token hasn't expired

**2. Model Not Supported Error**

```
Error: The requested model 'model-name' is not supported
```

**Solution:**
- Use a supported model like `meta-llama/Llama-3.2-3B-Instruct`
- Check model availability at https://huggingface.co/docs/api-inference

**3. Connection Timeout**

```
Error: Request timeout
```

**Solution:**
- Check internet connection
- Verify firewall settings
- Try again (API may be temporarily busy)

### Testing the API

**Direct curl test:**
```bash
curl https://router.huggingface.co/v1/chat/completions \
    -H "Authorization: Bearer $HF_TOKEN" \
    -H 'Content-Type: application/json' \
    -d '{
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "meta-llama/Llama-3.2-3B-Instruct"
    }'
```

**Expected response:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      }
    }
  ]
}
```

## Best Practices

### 1. Model Selection

- Use `Llama-3.2-3B-Instruct` for best Tamil support
- Consider `Llama-3.2-1B-Instruct` for faster responses
- Check model availability before deployment

### 2. Error Handling

- Always check response status code
- Handle rate limits gracefully
- Implement retry logic for transient errors
- Log errors for debugging

### 3. Token Management

- Store tokens securely in `.env` file
- Never commit tokens to version control
- Rotate tokens periodically
- Use read-only tokens when possible

### 4. Performance Optimization

- Cache responses when appropriate
- Use appropriate `max_tokens` limits
- Adjust `temperature` for use case
- Monitor API usage and costs

## Integration with RAG Pipeline

The Chat Completions API integrates seamlessly with the RAG pipeline:

```python
from backend.models import get_llm, initialize_llm
from backend.rag import get_rag_prompt_builder

# Initialize LLM (cloud mode)
llm = get_llm()
initialize_llm()

# Build RAG prompt with context
prompt_builder = get_rag_prompt_builder()
rag_prompt = prompt_builder.build_with_context(
    question="செயற்கை நுண்ணறிவு என்றால் என்ன?",
    context_documents=retrieved_docs
)

# Generate answer using cloud LLM
answer = llm.generate(rag_prompt)
```

## Future Enhancements

- [ ] Streaming support for real-time responses
- [ ] Automatic model fallback on errors
- [ ] Response caching for common queries
- [ ] Usage tracking and cost monitoring
- [ ] Support for additional providers
- [ ] Fine-tuning integration

## References

- [HuggingFace Chat Completions API](https://huggingface.co/docs/api-inference/detailed_parameters#chat-completion-api)
- [Llama 3.2 Models](https://huggingface.co/meta-llama)
- [API Authentication](https://huggingface.co/docs/api-inference/quicktour#authentication)
- [Project Documentation](./llm-configuration.md)

## Summary

The HuggingFace Chat Completions API provides a robust cloud-based LLM solution with:

✅ OpenAI-compatible interface  
✅ Excellent Tamil language support via Llama 3.2  
✅ Simple authentication with API tokens  
✅ Seamless integration with existing codebase  
✅ Dual-mode operation with local fallback  

**Key Takeaway:** Use `meta-llama/Llama-3.2-3B-Instruct` for production deployments requiring Tamil language support, and ensure the environment variable is named `HF_TOKEN` (not `HF_API_TOKEN`).
