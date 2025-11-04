# HuggingFace Inference API Setup Guide

This guide helps you set up **HuggingFace Inference API** for running Tamil-friendly language models without local resources.

## Why HuggingFace Inference API?

✅ **No local downloads** - Models run on HuggingFace servers
✅ **No RAM/GPU needed** - Zero local compute requirements
✅ **Fast inference** - Optimized HuggingFace infrastructure
✅ **Free tier available** - No cost for moderate usage
✅ **Easy model switching** - Change models instantly
✅ **Better Tamil support** - Access to latest multilingual models

## Recommended Models for Tamil

### Option 1: bigscience/bloomz-1b1 (Default, Recommended)
- **Size**: 1.1B parameters
- **Languages**: 46+ including Tamil, English, Hindi
- **Quality**: Good Tamil support, instruction-tuned
- **Speed**: Fast
- **Best for**: General purpose, multilingual tasks

### Option 2: sarvamai/sarvam-2b-v0.5
- **Size**: 2B parameters
- **Languages**: Indian languages (Tamil, Hindi, etc.)
- **Quality**: Excellent Tamil support
- **Speed**: Medium
- **Best for**: Best Tamil quality, Indian language focus

### Option 3: bigscience/bloomz-560m
- **Size**: 560M parameters
- **Languages**: 46+ multilingual
- **Quality**: Decent Tamil support
- **Speed**: Very fast
- **Best for**: Fastest responses, lower quality okay

### Option 4: google/gemma-2b-it
- **Size**: 2B parameters
- **Languages**: Multilingual including Tamil
- **Quality**: Good general quality
- **Speed**: Medium
- **Best for**: Balance of quality and speed

## Quick Setup (3 Steps)

### Step 1: Get Free API Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it: "tamil-ai-assistant"
4. Type: "Read"
5. Click "Generate"
6. Copy the token (starts with `hf_...`)

### Step 2: Set Environment Variable

**Linux/Mac:**
```bash
# Temporary (current session only)
export HF_API_TOKEN='hf_your_token_here'

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export HF_API_TOKEN="hf_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:HF_API_TOKEN='hf_your_token_here'
```

**Or use .env file:**
```bash
# Create .env file in project root
echo 'HF_API_TOKEN=hf_your_token_here' >> .env
```

### Step 3: Test the Setup

```bash
# Test HuggingFace API connection
python backend/models/llm_huggingface.py
```

**Expected output:**
```
🧪 Testing HuggingFace Inference API
🔧 Connecting to HuggingFace Inference API...
   Model: bigscience/bloomz-1b1
✅ Connected to HuggingFace Inference API!
   Using model: bigscience/bloomz-1b1

🧪 Test: Text Generation
Prompt: வணக்கம்! செயற்கை நுண்ணறிவு என்றால் என்ன?
🤖 Generating response via HuggingFace API...
✅ Generation complete!
Response:
[Tamil answer about AI...]
```

## Running the Demo

Once setup is complete:

```bash
# Run complete RAG demo
python demo_rag_qa.py

# Or query directly
python query_rag.py "செயற்கை நுண்ணறிவு என்றால் என்ன?"

# Interactive mode
python query_rag.py
```

## Switching Models

To use a different model, update `backend/settings.py`:

```python
# Change this line:
HF_MODEL_NAME: str = "bigscience/bloomz-1b1"

# To one of these:
# HF_MODEL_NAME: str = "sarvamai/sarvam-2b-v0.5"  # Best Tamil
# HF_MODEL_NAME: str = "bigscience/bloomz-560m"   # Fastest
# HF_MODEL_NAME: str = "google/gemma-2b-it"        # Good balance
```

Or set via environment variable:
```bash
export HF_MODEL_NAME="sarvamai/sarvam-2b-v0.5"
```

## Verification

Check if everything is working:

```bash
# 1. Verify token is set
echo $HF_API_TOKEN

# Should show: hf_...

# 2. Test API connection
python backend/models/llm_huggingface.py

# 3. Run demo
python demo_rag_qa.py
```

## Troubleshooting

### Error: "HF_API_TOKEN not set"

**Solution:** Set the environment variable:
```bash
export HF_API_TOKEN='hf_your_token_here'
```

### Error: "Authentication failed. Invalid API token"

**Solutions:**
1. Check token is correct (copy from HuggingFace)
2. Token should start with `hf_`
3. Regenerate token if needed

### Error: "Model not found"

**Solutions:**
1. Check model name is correct
2. Verify model exists on HuggingFace
3. Check model has inference API enabled (look for ⚡ icon)

### Error: "Model is loading" or 503 error

**Solution:** Model is cold-starting (first use). Wait 10-30 seconds and try again.

### Slow responses

**Solutions:**
1. Use smaller model: `bigscience/bloomz-560m`
2. Reduce `max_tokens` in settings.py
3. Model may be experiencing high traffic

### Rate limiting

**Solutions:**
1. Get API token (free tier has higher limits)
2. Wait a few minutes before retrying
3. Consider upgrading to paid tier for higher limits

## API Limits

**Free tier (with token):**
- ✅ Reasonable rate limits
- ✅ Most models available
- ✅ Sufficient for development/testing

**Free tier (without token):**
- ⚠️ Strict rate limits
- ⚠️ May experience delays
- ⚠️ Limited for production

**Paid tier:**
- ✅ Higher rate limits
- ✅ Priority access
- ✅ Better for production

## Privacy & Security

✅ **API Token Security:**
- Never commit tokens to git
- Use environment variables or .env files
- Regenerate tokens if exposed

✅ **Data Privacy:**
- Your prompts are sent to HuggingFace servers
- Subject to HuggingFace privacy policy
- Consider this for sensitive data

✅ **Offline Alternative:**
- If privacy is critical, use Ollama (local inference)
- See CLAUDE.md for Ollama setup

## Model Comparison

| Model | Size | Tamil Quality | Speed | Memory | Best For |
|-------|------|---------------|-------|--------|----------|
| **bloomz-1b1** | 1.1B | ⭐⭐⭐⭐ | Fast | None | **Recommended default** |
| **sarvam-2b-v0.5** | 2B | ⭐⭐⭐⭐⭐ | Medium | None | **Best Tamil quality** |
| **bloomz-560m** | 560M | ⭐⭐⭐ | Very Fast | None | **Speed priority** |
| **gemma-2b-it** | 2B | ⭐⭐⭐⭐ | Medium | None | Good balance |

## Costs

**HuggingFace Inference API:**
- Free tier: ✅ Free (with rate limits)
- Pro tier: ~$9/month (higher limits)
- Enterprise: Custom pricing

**Comparison with Ollama:**
- Ollama: Free but needs ~4GB RAM locally
- HuggingFace: Free tier, zero local resources

## Advanced Configuration

### Custom Parameters

Edit `backend/models/llm_huggingface.py` to adjust generation parameters:

```python
payload = {
    "inputs": prompt,
    "parameters": {
        "max_new_tokens": 512,      # Adjust max length
        "temperature": 0.7,          # 0=deterministic, 1=creative
        "top_p": 0.95,              # Nucleus sampling
        "top_k": 50,                # Top-k sampling
        "repetition_penalty": 1.1,  # Prevent repetition
    }
}
```

### Timeout Adjustment

For longer responses, increase timeout:

```python
# In llm_huggingface.py, line ~200
response = requests.post(
    self.api_url,
    headers=headers,
    json=payload,
    timeout=120  # Increase from 60 to 120 seconds
)
```

## Next Steps

After HuggingFace API is working:
1. ✅ Test with Tamil queries
2. ✅ Run full demo: `python demo_rag_qa.py`
3. ✅ Try different models for quality/speed trade-offs
4. ✅ Ingest your own documents via Admin API
5. 🔄 Continue with Phase 5: Speech Processing

## Resources

- **HuggingFace Hub**: https://huggingface.co/models
- **Inference API Docs**: https://huggingface.co/docs/api-inference
- **Get API Token**: https://huggingface.co/settings/tokens
- **Model Cards**: Check each model's page for details

---

**Need help?** Check CLAUDE.md or create an issue in the repository.
