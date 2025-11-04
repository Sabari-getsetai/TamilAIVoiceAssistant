# Models Information

This document explains where models are stored and how they're loaded.

## Model Storage Locations

### 1. LLM (Tamil-LLaMA)
- **Location:** `models/llm/tamil-llama-7b-v0.1-q4_k_m.gguf`
- **Size:** 3.9 GB
- **Storage:** Local project directory
- **Why:** GGUF models are typically loaded from local files

### 2. STT (Faster-Whisper)
- **Location:** `~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v2`
- **Size:** 2.9 GB
- **Storage:** HuggingFace cache (system-wide)
- **Why:** faster-whisper uses HuggingFace's caching system

### 3. TTS (MMS-Tamil)
- **Location:** `~/.cache/huggingface/hub/models--facebook--mms-tts-tam`
- **Size:** 139 MB
- **Storage:** HuggingFace cache (system-wide)
- **Why:** Transformers library uses HuggingFace's caching system

### 4. Embeddings (SentenceTransformers)
- **Location:** `~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2`
- **Size:** ~400 MB
- **Storage:** HuggingFace cache (system-wide)
- **Why:** sentence-transformers uses HuggingFace's caching system

## Why Different Storage Methods?

### HuggingFace Cache Benefits:
- ✅ **No Duplicates:** Same model used across multiple projects
- ✅ **Automatic Updates:** Easy to update models
- ✅ **Standard Practice:** Industry standard for Python AI libraries
- ✅ **Version Management:** Handles different model versions automatically

### Local Storage (LLM):
- ✅ **Portability:** Easy to package with application
- ✅ **Control:** Full control over model file
- ✅ **GGUF Standard:** GGUF models typically loaded from local paths

## Verifying Models

### Check All Models:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run verification
python -c "
from sentence_transformers import SentenceTransformer
from transformers import VitsModel, AutoTokenizer
from faster_whisper import WhisperModel
from pathlib import Path

# Check each model
print('✅ Embeddings:', SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'))
print('✅ TTS:', VitsModel.from_pretrained('facebook/mms-tts-tam'))
print('✅ STT:', WhisperModel('large-v2', device='cpu'))
print('✅ LLM:', list(Path('models/llm').glob('*.gguf')))
"
```

### Check HuggingFace Cache:
```bash
ls -lh ~/.cache/huggingface/hub/
```

### Check LLM:
```bash
ls -lh models/llm/
```

## Total Disk Usage

| Model | Size | Location |
|-------|------|----------|
| LLM | 3.9 GB | Project |
| STT | 2.9 GB | Cache |
| TTS | 139 MB | Cache |
| Embeddings | 400 MB | Cache |
| **Total** | **~7.3 GB** | Mixed |

## Offline Operation

All models work **100% offline** once downloaded:
- ✅ LLM: Loaded from local file
- ✅ STT: Loaded from cache (no internet needed)
- ✅ TTS: Loaded from cache (no internet needed)
- ✅ Embeddings: Loaded from cache (no internet needed)

## Troubleshooting

### Models Not Found?
```bash
# Re-download all models
python backend/models/download_models.py
```

### Clear Cache?
```bash
# Remove HuggingFace cache (will need to re-download)
rm -rf ~/.cache/huggingface/
```

### Move Models to Project?
If you want all models in the project directory for portability:
```bash
# Copy from cache to project (optional)
cp -r ~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v2 models/stt/
cp -r ~/.cache/huggingface/hub/models--facebook--mms-tts-tam models/tts/
```

**Note:** This is not recommended unless you need a fully portable deployment package.

## Tamil Language Support

✅ **All models support Tamil:**
- **LLM:** Tamil-LLaMA (native Tamil support)
- **STT:** Whisper large-v2 (100+ languages including Tamil)
- **TTS:** MMS-TTS Tamil (native Tamil voice)
- **Embeddings:** Multilingual (supports Tamil + code-mixing)
