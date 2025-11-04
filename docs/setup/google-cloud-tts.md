# Google Cloud Text-to-Speech Setup Guide

Complete guide to setting up premium Google Cloud Text-to-Speech for Tamil AI Voice Assistant.

## Overview

This project now supports **dual-mode TTS**:

1. **Google Cloud TTS (Premium)** - Chirp3 HD and WaveNet neural voices with natural prosody
2. **gTTS (Free Fallback)** - Basic TTS with audio enhancements

The system automatically falls back to gTTS if Google Cloud credentials are not configured.

## Why Upgrade to Google Cloud TTS?

| Feature | gTTS (Free) | Google Cloud Chirp3 HD |
|---------|-------------|------------------------|
| Voice Quality | Synthetic | Ultra-natural, human-like |
| Prosody & Intonation | Basic | Advanced (context-aware) |
| Tamil Pronunciation | Good | Excellent |
| Naturalness | Basic | Ultra-high (latest AI models) |
| Customization | Limited | High (rate, pitch, effects) |
| Latency | ~1-2s | ~0.5-1s |
| Cost | Free | Pay-as-you-go (free tier available) |
| Setup Complexity | Simple | Moderate |

## Google Cloud TTS Features

### Available Tamil Voices

| Voice Name | Gender | Quality | Description |
|------------|--------|---------|-------------|
| **`ta-IN-Chirp3-HD-Callirrhoe`** | **Female** | **Ultra-High (Chirp3 HD)** | **Default voice** ⭐ Latest |
| `ta-IN-Chirp3-HD-Achernar` | Female | Ultra-High (Chirp3 HD) | Alternative premium voice |
| `ta-IN-Wavenet-B` | Female | Premium (WaveNet) | WaveNet neural TTS |
| `ta-IN-Wavenet-A` | Male | Premium (WaveNet) | WaveNet neural TTS |
| `ta-IN-Standard-A` | Male | Standard | Standard quality |
| `ta-IN-Standard-B` | Female | Standard | Standard quality |

### Voice Customization

```python
# Speaking rate (0.25 to 4.0)
tts.set_speaking_rate(1.2)  # 20% faster

# Pitch adjustment (-20 to +20 semitones)
tts.set_pitch(-2.0)  # Slightly lower pitch
```

## Setup Instructions

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name (e.g., `tamil-voice-assistant`)
4. Click **Create**
5. Wait for project to be created (~30 seconds)

### Step 2: Enable Text-to-Speech API

1. In Google Cloud Console, ensure your project is selected
2. Go to **APIs & Services** → **Library**
3. Search for **"Cloud Text-to-Speech API"**
4. Click on it → Click **Enable**
5. Wait for API to be enabled (~10 seconds)

### Step 3: Create Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Enter details:
   - **Name**: `tamil-tts-service`
   - **Description**: `Service account for Tamil TTS`
4. Click **Create and Continue**
5. Grant role: **Cloud Text-to-Speech User**
6. Click **Continue** → **Done**

### Step 4: Create and Download JSON Key

1. In Service Accounts list, find `tamil-tts-service`
2. Click the three dots (⋮) → **Manage keys**
3. Click **Add Key** → **Create new key**
4. Select **JSON** format
5. Click **Create**
6. JSON key file will download automatically
7. **IMPORTANT**: Save this file securely (e.g., `~/credentials/tamil-tts-key.json`)

### Step 5: Configure Environment

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file:**
   ```env
   # Enable Google Cloud TTS
   USE_GOOGLE_CLOUD_TTS=true

   # Set voice name (latest Chirp3 HD ultra-high quality)
   TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe

   # Set your Google Cloud project ID
   GOOGLE_CLOUD_PROJECT_ID=your-project-id-here

   # Set path to service account JSON key
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json
   ```

3. **Replace with your values:**
   - `GOOGLE_CLOUD_PROJECT_ID`: Your project ID from Google Cloud Console
   - `GOOGLE_APPLICATION_CREDENTIALS`: Absolute path to downloaded JSON key

### Step 6: Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install Google Cloud TTS
pip install google-cloud-texttospeech
```

### Step 7: Test Setup

```bash
# Test TTS with sample Tamil texts
python backend/speech/tts.py
```

**Expected output:**
```
✅ Google Cloud TTS ready!
   Voice: ta-IN-Chirp3-HD-Callirrhoe
   Language: ta-IN
   Quality: Chirp3 HD (Ultra-High Quality)
```

If you see this, **congratulations!** 🎉 Google Cloud TTS is working.

## Troubleshooting

### Error: "Google Cloud credentials not found"

**Solution:**
1. Check that `GOOGLE_APPLICATION_CREDENTIALS` points to valid JSON file
2. Ensure path is absolute (not relative)
3. Verify file has correct permissions:
   ```bash
   chmod 600 /path/to/service-account-key.json
   ```

### Error: "Permission denied" or "403 Forbidden"

**Solution:**
1. Ensure Text-to-Speech API is enabled in Google Cloud Console
2. Verify service account has **Cloud Text-to-Speech User** role
3. Wait 1-2 minutes for permissions to propagate

### Error: "Invalid credentials"

**Solution:**
1. Re-download service account JSON key
2. Ensure JSON file is not corrupted
3. Verify `GOOGLE_CLOUD_PROJECT_ID` matches your actual project ID

### Falls back to gTTS

**Behavior:**
```
⚠️  Google Cloud credentials not found
⚠️  Falling back to gTTS...
```

**This is normal** if:
- You haven't set up Google Cloud credentials yet
- `USE_GOOGLE_CLOUD_TTS=false` in .env
- Credentials are invalid/expired

The system gracefully falls back to free gTTS.

## Pricing

### Free Tier
- **4 million characters/month** free (WaveNet voices)
- **1 million characters/month** free (Standard voices)
- More than enough for personal/development use

### Paid Pricing (after free tier)
- **WaveNet voices**: $16 per 1 million characters
- **Standard voices**: $4 per 1 million characters

**Example usage:**
- Average Tamil sentence: ~50 characters
- 4M chars = ~80,000 sentences/month free
- ~2,600 sentences/day free

For most personal projects, **you'll stay within free tier**.

[Check current pricing](https://cloud.google.com/text-to-speech/pricing)

## Usage Examples

### Basic Synthesis

```python
from backend.speech.tts import get_tts_engine, initialize_tts

# Initialize TTS
initialize_tts()
tts = get_tts_engine()

# Synthesize Tamil speech
text = "வணக்கம்! நான் தமிழ் பேசும் AI உதவியாளர்."
audio = tts.synthesize(text, output_path="output.wav")
```

### Customize Voice Parameters

```python
from backend.speech.tts import GoogleCloudTTS

# Create custom TTS engine with Chirp3 HD voice
tts = GoogleCloudTTS(
    voice_name="ta-IN-Chirp3-HD-Callirrhoe",
    language_code="ta-IN",
    speaking_rate=1.1,  # 10% faster
    pitch=-1.5          # Slightly lower pitch
)

tts.load_model()
tts.synthesize("உங்களுக்கு எப்படி உதவ முடியும்?", "greeting.wav")
```

### Batch Processing

```python
from backend.speech.tts import get_tts_engine

tts = get_tts_engine()

texts = [
    "வணக்கம்!",
    "நான் உங்களுக்கு எப்படி உதவ முடியும்?",
    "நன்றி! வணக்கம்."
]

# Synthesize all texts
output_paths = tts.synthesize_batch(texts, output_dir="data/out")
```

## Fallback Configuration

To use **only gTTS** (no Google Cloud):

```env
# .env file
USE_GOOGLE_CLOUD_TTS=false
```

The system will skip Google Cloud TTS and use gTTS directly.

## Security Best Practices

1. **Never commit credentials to git:**
   ```bash
   # .gitignore already includes:
   *.json      # Service account keys
   .env        # Environment variables
   ```

2. **Restrict file permissions:**
   ```bash
   chmod 600 ~/credentials/tamil-tts-key.json
   ```

3. **Use environment variables:**
   Set `GOOGLE_APPLICATION_CREDENTIALS` in environment instead of `.env`:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

4. **Rotate keys periodically:**
   - Create new service account key every 90 days
   - Delete old keys from Google Cloud Console

## Voice Comparison

Test different voices to find your preference:

```bash
# Edit .env and change TTS_MODEL_NAME
# Then test:
python backend/speech/tts.py
```

**Voice recommendations:**
- **Ultra-high quality (Latest)**: `ta-IN-Chirp3-HD-Callirrhoe` or `ta-IN-Chirp3-HD-Achernar` (Chirp3 HD)
- **Premium quality**: `ta-IN-Wavenet-B` (female) or `ta-IN-Wavenet-A` (male) (WaveNet)
- **Cost-effective**: `ta-IN-Standard-B` (female) or `ta-IN-Standard-A` (male) (Standard)
- **Free**: Use `USE_GOOGLE_CLOUD_TTS=false` for gTTS

## Monitoring Usage

Track your Text-to-Speech API usage:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Dashboard**
3. Click **Cloud Text-to-Speech API**
4. View **Quotas** and **Metrics**

Set up billing alerts to avoid unexpected charges:

1. Go to **Billing** → **Budgets & alerts**
2. Create budget with monthly limit (e.g., $5)
3. Set alert threshold at 50%, 90%, 100%

## Additional Resources

- [Google Cloud TTS Documentation](https://cloud.google.com/text-to-speech/docs)
- [Tamil Voice Samples](https://cloud.google.com/text-to-speech/docs/voices)
- [SSML Guide](https://cloud.google.com/text-to-speech/docs/ssml) - Advanced voice markup
- [Pricing Calculator](https://cloud.google.com/products/calculator)

## Support

If you encounter issues:

1. Check error messages in console output
2. Review this guide's troubleshooting section
3. Verify Google Cloud Console settings
4. Test with gTTS fallback (`USE_GOOGLE_CLOUD_TTS=false`)

For Google Cloud issues:
- [Support](https://cloud.google.com/support)
- [Community Forums](https://www.googlecloudcommunity.com/)

---

**Happy voice synthesis!** 🎤🔊
