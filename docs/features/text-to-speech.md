# How to Enable Google Cloud Text-to-Speech API

Your Tamil AI Voice Assistant is currently using **gTTS (free fallback)**. To unlock premium WaveNet voices, follow these steps:

## Current Status

✅ **Working**: gTTS fallback (free, internet-required)
⏸️ **Pending**: Google Cloud TTS (premium WaveNet voices)

**Why pending?** The Text-to-Speech API needs to be enabled in your Google Cloud project.

---

## Step-by-Step Guide

### Step 1: Enable the Text-to-Speech API

**Option A: Direct Link (Easiest)**

Click this link and click "Enable":

🔗 **https://console.developers.google.com/apis/api/texttospeech.googleapis.com/overview?project=795966264458**

**Option B: Via Google Cloud Console**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: **cs-poc-yoepgevc6olhu3zg9ruup5c**
3. Click **☰ Menu** → **APIs & Services** → **Library**
4. Search for: **"Cloud Text-to-Speech API"**
5. Click on the API
6. Click **"ENABLE"** button
7. Wait 1-2 minutes for activation

### Step 2: Verify API is Enabled

1. Go to **APIs & Services** → **Dashboard**
2. Look for **"Cloud Text-to-Speech API"** in the enabled APIs list
3. If you see it there, you're good to go!

### Step 3: Update Configuration

Edit your `.env` file and change:

```bash
# From:
USE_GOOGLE_CLOUD_TTS=false

# To:
USE_GOOGLE_CLOUD_TTS=true
```

### Step 4: Test Premium Voice

Run the test script:

```bash
source .venv/bin/activate
python backend/speech/tts.py
```

**Expected output:**
```
✅ Google Cloud TTS ready!
   Voice: ta-IN-Wavenet-B
   Language: ta-IN
   Quality: WaveNet (Premium Neural TTS)
```

---

## Troubleshooting

### Error: "API has not been enabled"

**Solution:** Complete Step 1 above. Wait 2-3 minutes after enabling.

### Error: "Permission denied" or "403 Forbidden"

**Possible causes:**

1. **API not enabled** → Enable via Step 1
2. **Permissions not propagated** → Wait 5 minutes and retry
3. **Service account lacks permissions** → Add "Cloud Text-to-Speech User" role:
   - Go to **IAM & Admin** → **Service Accounts**
   - Find: `tts-service-account@cs-poc-yoepgevc6olhu3zg9ruup5c.iam.gserviceaccount.com`
   - Click **⋮** → **Manage permissions**
   - Add role: **Cloud Text-to-Speech User**

### Error: "Credentials not found"

Your credentials are already configured correctly at:
```
credentials/google-cloud-tts-key.json
```

If you still see this error, verify the file exists:
```bash
ls -la credentials/google-cloud-tts-key.json
```

### Still Not Working?

**Fallback to gTTS:**

The system automatically falls back to gTTS if Google Cloud TTS fails. You can continue using the assistant with gTTS while troubleshooting.

To force gTTS mode:
```bash
# .env file
USE_GOOGLE_CLOUD_TTS=false
```

---

## Cost & Billing

### Free Tier
- **4 million WaveNet characters/month** FREE
- **1 million Standard characters/month** FREE

### Estimated Usage

Average Tamil sentence: ~50 characters

**Examples:**
- 100 voice responses/day = ~5,000 chars/day = 150,000 chars/month
- **Result:** Well within free tier! 💰

### Enable Billing (Required)

Even for free tier usage, you need to enable billing:

1. Go to [Google Cloud Billing](https://console.cloud.google.com/billing)
2. Link a billing account (credit card required for verification)
3. Google won't charge unless you exceed free tier
4. Set up budget alerts at $1, $5, $10 to avoid surprises

**Tip:** Create a billing alert:
- Go to **Billing** → **Budgets & alerts**
- Set budget: $5/month
- Alert thresholds: 50%, 90%, 100%

---

## Verification Checklist

Before testing, verify:

- [ ] Text-to-Speech API is enabled in Google Cloud Console
- [ ] Service account has "Cloud Text-to-Speech User" role
- [ ] Billing is enabled (required even for free tier)
- [ ] Waited 2-3 minutes after enabling API
- [ ] `.env` has `USE_GOOGLE_CLOUD_TTS=true`
- [ ] Credentials file exists at `credentials/google-cloud-tts-key.json`

---

## Quick Test

Once API is enabled, run:

```bash
# Test synthesis
python -c "
from backend.speech.tts import synthesize_speech
audio = synthesize_speech('வணக்கம்!', 'test.wav')
print('✅ Success!' if audio is not None else '❌ Failed')
"
```

---

## Benefits of Google Cloud TTS

Once enabled, you'll get:

| Feature | gTTS | Google Cloud WaveNet |
|---------|------|---------------------|
| Voice Quality | Synthetic | Natural, human-like |
| Prosody | Basic | Advanced |
| Customization | None | Rate, pitch, effects |
| Latency | ~1-2s | ~0.5-1s |
| Tamil Accuracy | Good | Excellent |

---

## Support Links

- [Enable API Direct Link](https://console.developers.google.com/apis/api/texttospeech.googleapis.com/overview?project=795966264458)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Text-to-Speech Documentation](https://cloud.google.com/text-to-speech/docs)
- [Pricing Details](https://cloud.google.com/text-to-speech/pricing)

---

## Summary

**Current Setup:**
- ✅ Credentials configured
- ✅ gTTS working (fallback)
- ⏸️ API needs to be enabled

**Next Action:**
1. Click [this link](https://console.developers.google.com/apis/api/texttospeech.googleapis.com/overview?project=795966264458)
2. Click "Enable"
3. Wait 2 minutes
4. Change `USE_GOOGLE_CLOUD_TTS=true` in `.env`
5. Test with `python backend/speech/tts.py`

That's it! Once the API is enabled, you'll have premium WaveNet Tamil voice. 🎤
