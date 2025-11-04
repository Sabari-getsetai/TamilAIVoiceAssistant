# Female Voice TTS Setup - Tamil AI Voice Assistant

## Overview

The Tamil AI Voice Assistant now uses **Google Text-to-Speech (gTTS)** with a clear, precise **female voice** for Tamil language synthesis.

## What Changed

### Previous Setup
- **Engine**: Meta's MMS-TTS (Massively Multilingual Speech)
- **Voice**: Single voice (no gender option)
- **Limitations**: Limited voice customization

### New Setup
- **Engine**: Google Text-to-Speech (gTTS)
- **Voice**: Female voice with Indian Tamil accent
- **Benefits**: 
  - ✅ Clear and precise pronunciation
  - ✅ Natural-sounding female voice
  - ✅ Better Tamil accent (Indian)
  - ✅ High-quality audio output
  - ✅ Python 3.12 compatible

## Installation

### 1. Install Required Packages

```bash
pip install gtts>=2.5.0 pydub>=0.25.1
```

### 2. Install ffmpeg (Required for Audio Processing)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

## Usage

### Basic Usage

```python
from backend.speech import synthesize_speech

# Synthesize Tamil text to speech
text = "வணக்கம்! நான் தமிழ் பேசும் செயற்கை நுண்ணறிவு உதவியாளர்."
audio = synthesize_speech(text, output_path="output.wav")
```

### Advanced Usage

```python
from backend.speech import GoogleTTS

# Create TTS instance
tts = GoogleTTS(
    lang="ta",           # Tamil language
    slow=False,          # Normal speed (set True for slower, clearer speech)
    tld="co.in"          # Indian accent
)

# Load the engine
tts.load_model()

# Synthesize speech
audio = tts.synthesize(
    text="உங்களுக்கு எப்படி உதவ முடியும்?",
    output_path="greeting.wav",
    sample_rate=24000
)
```

### Adjusting Voice Clarity

For even clearer speech (slower pace):

```python
from backend.speech import get_tts_engine

tts = get_tts_engine()
tts.set_speed(slow=True)  # Enable slow, clear speech

# Now all synthesis will be slower and clearer
audio = tts.synthesize("தெளிவான குரல்")
```

## Voice Characteristics

### Female Voice Features
- **Gender**: Female
- **Accent**: Indian Tamil
- **Clarity**: High (optimized for clear pronunciation)
- **Speed**: Adjustable (normal or slow)
- **Sample Rate**: 24kHz (high quality)
- **Format**: WAV (16-bit PCM)

### Quality Settings

The voice is configured for:
- Clear pronunciation of Tamil words
- Natural intonation and rhythm
- Proper handling of Tamil script
- Consistent audio quality

## Testing

Test the new voice:

```bash
python backend/speech/tts.py
```

This will generate 3 test audio files in `data/out/`:
- `test_gtts_1.wav` - Greeting
- `test_gtts_2.wav` - AI explanation
- `test_gtts_3.wav` - Weather question

## Integration with Voice Assistant

The new TTS is automatically integrated with:
- WebSocket voice interface (`/ws/voice`)
- Chat API (`/api/chat`)
- Admin dashboard

No code changes needed - the voice assistant will automatically use the new female voice!

## Configuration

### Environment Variables

No additional environment variables needed. The TTS uses default settings optimized for Tamil female voice.

### Customization Options

You can customize in `backend/speech/tts.py`:

```python
# In get_tts_engine() function
_tts_instance = GoogleTTS(
    lang="ta",           # Language
    slow=False,          # Speed (False=normal, True=slow)
    tld="co.in"          # Accent (co.in=Indian, com=US, co.uk=UK)
)
```

## Performance

- **Synthesis Speed**: ~1-2 seconds for typical sentences
- **Audio Quality**: 24kHz, 16-bit PCM
- **Internet Required**: Yes (gTTS uses Google's cloud service)
- **Caching**: Recommended for frequently used phrases

## Troubleshooting

### Issue: "ffmpeg not found"
**Solution**: Install ffmpeg (see Installation section)

### Issue: "No internet connection"
**Solution**: gTTS requires internet. Ensure you have an active connection.

### Issue: Voice sounds robotic
**Solution**: Try enabling slow mode for more natural speech:
```python
tts.set_speed(slow=True)
```

### Issue: Audio quality is poor
**Solution**: Check sample rate is set to 24000 Hz (default)

## Comparison: Old vs New

| Feature | MMS-TTS (Old) | gTTS (New) |
|---------|---------------|------------|
| Voice Gender | Neutral | Female |
| Clarity | Good | Excellent |
| Accent | Generic | Indian Tamil |
| Speed Control | No | Yes |
| Internet Required | No | Yes |
| Python 3.12 Support | No | Yes |
| Audio Quality | 16kHz | 24kHz |

## Next Steps

1. ✅ Test the voice with your application
2. ✅ Adjust speed if needed for clarity
3. ✅ Consider caching frequently used phrases
4. ✅ Monitor internet connectivity for production use

## Support

For issues or questions:
- Check the test output: `python backend/speech/tts.py`
- Review logs in the console
- Ensure ffmpeg is installed: `ffmpeg -version`

---

**Note**: The female voice provides a more natural and engaging user experience for the Tamil AI Voice Assistant. The clear pronunciation and Indian accent make it ideal for Tamil language interactions.
