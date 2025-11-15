"""
Text-to-Speech (TTS) for Tamil AI Voice Assistant

Supports dual-mode TTS:
1. Google Cloud Text-to-Speech API (Premium WaveNet voices)
2. gTTS fallback (Free, internet-required)

Features:
- High-quality Tamil WaveNet female voice (ta-IN-Wavenet-B)
- Natural prosody and intonation
- Fast synthesis with cloud-based processing
- Automatic fallback to gTTS if credentials not available
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union
import numpy as np
from io import BytesIO


from backend.settings import settings
from backend.speech.audio_utils import save_audio


class GoogleCloudTTS:
    """
    Google Cloud Text-to-Speech engine for Tamil with Premium Voices

    Features:
    - Chirp3 HD voices (ta-IN-Chirp3-HD-*) - Latest ultra-high quality
    - WaveNet voices (ta-IN-Wavenet-*) - Premium neural TTS
    - Natural female voices with high-quality prosody
    - Advanced speech synthesis with neural networks
    - Clear and precise Tamil pronunciation
    - Fast cloud-based inference

    Supported Voice Types:
    - Chirp3 HD: Latest generation, ultra-natural
    - WaveNet: Premium quality, neural TTS
    - Standard: Good quality, cost-effective

    Voice Characteristics:
    - ta-IN-Chirp3-HD-Callirrhoe: Ultra-high quality, natural female
    - ta-IN-Chirp3-HD-Achernar: Ultra-high quality, alternative female
    - ta-IN-Wavenet-B: Premium WaveNet female
    - ta-IN-Wavenet-A: Premium WaveNet male
    """

    def __init__(
        self,
        voice_name: str = "ta-IN-Chirp3-HD-Callirrhoe",
        language_code: str = "ta-IN",
        speaking_rate: float = 1.0,
        pitch: float = 0.0
    ):
        """
        Initialize Google Cloud TTS engine

        Args:
            voice_name: Voice name (default: ta-IN-Chirp3-HD-Callirrhoe)
                       Options: ta-IN-Chirp3-HD-Callirrhoe, ta-IN-Chirp3-HD-Achernar,
                               ta-IN-Wavenet-B, ta-IN-Wavenet-A
            language_code: Language and region code
            speaking_rate: Speech speed (0.25 to 4.0, default 1.0)
            pitch: Voice pitch in semitones (-20.0 to 20.0, default 0.0)
        """
        self.voice_name = voice_name
        self.language_code = language_code
        self.speaking_rate = speaking_rate
        self.pitch = pitch
        self.client = None
        self.is_loaded = False

        # Determine voice type for display
        if "Chirp3-HD" in voice_name:
            self.voice_type = "Chirp3 HD (Ultra-High Quality)"
        elif "Wavenet" in voice_name:
            self.voice_type = "WaveNet (Premium Neural TTS)"
        else:
            self.voice_type = "Standard"

    def load_model(self) -> bool:
        """
        Initialize the Google Cloud TTS client

        Returns:
            True if initialized successfully
        """
        try:
            from google.cloud import texttospeech

            # Check for credentials
            if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                if settings.GOOGLE_APPLICATION_CREDENTIALS:
                    # Convert relative path to absolute path
                    creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS
                    if not os.path.isabs(creds_path):
                        creds_path = str(settings.PROJECT_ROOT / creds_path)

                    # Verify file exists
                    if not os.path.exists(creds_path):
                        print(f"⚠️  Google Cloud credentials file not found: {creds_path}")
                        print("   Check GOOGLE_APPLICATION_CREDENTIALS path in .env")
                        return False

                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                else:
                    print("⚠️  Google Cloud credentials not found")
                    print("   Set GOOGLE_APPLICATION_CREDENTIALS in .env or environment")
                    return False

            # Initialize client
            self.client = texttospeech.TextToSpeechClient()
            self.is_loaded = True

            print("✅ Google Cloud TTS ready!")
            print(f"   Voice: {self.voice_name}")
            print(f"   Language: {self.language_code}")
            print(f"   Quality: {self.voice_type}")

            return True

        except ImportError:
            print("❌ google-cloud-texttospeech not installed")
            print("   Install with: pip install google-cloud-texttospeech")
            return False
        except Exception as e:
            print(f"❌ Error initializing Google Cloud TTS: {e}")
            print("   Check your GOOGLE_APPLICATION_CREDENTIALS path")
            return False

    def _split_text_into_sentences(self, text: str, max_chars: int = 4500) -> list:
        """
        Split text into smaller chunks to avoid Google TTS sentence length limit

        Args:
            text: Text to split
            max_chars: Maximum characters per chunk (Google TTS limit is ~5000, use 4500 for safety)

        Returns:
            List of text chunks
        """
        import re

        # If text is short enough, return as-is
        if len(text) <= max_chars:
            return [text]

        # Tamil sentence delimiters: period, question mark, exclamation, Tamil purna virama, newline
        delimiters = r'[.!?।॥\n]+'

        # Split by sentence delimiters
        sentences = re.split(delimiters, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence exceeds limit, save current chunk and start new one
            if current_chunk and len(current_chunk) + len(sentence) + 2 > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def synthesize(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        sample_rate: int = 24000
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech from text using Google Cloud TTS

        Args:
            text: Tamil text to synthesize
            output_path: Optional path to save audio file
            sample_rate: Output sample rate (16000 or 24000)

        Returns:
            Audio data as numpy array (or None if failed)
        """
        if not self.is_loaded:
            raise RuntimeError("TTS not ready. Call load_model() first.")

        try:
            from google.cloud import texttospeech

            print(f"\n🔊 Synthesizing speech with Google Cloud TTS...")
            print(f"   Text: {text[:100]}...")
            print(f"   Voice: {self.voice_name} ({self.voice_type})")
            print(f"   Rate: {self.speaking_rate}x | Pitch: {self.pitch:+.1f} semitones")

            # Split text into chunks if too long
            text_chunks = self._split_text_into_sentences(text)

            if len(text_chunks) > 1:
                print(f"   ⚠️  Text split into {len(text_chunks)} chunks due to length")

            all_audio_chunks = []

            for i, chunk in enumerate(text_chunks):
                if len(text_chunks) > 1:
                    print(f"   📝 Processing chunk {i+1}/{len(text_chunks)}...")

                # Create synthesis input
                synthesis_input = texttospeech.SynthesisInput(text=chunk)

                # Configure voice parameters
                voice = texttospeech.VoiceSelectionParams(
                    language_code=self.language_code,
                    name=self.voice_name,
                    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
                )

                # Configure audio format - use pure Chirp3 HD output without processing
                # Note: Chirp3 HD voices don't support pitch adjustment (they're already optimized)
                audio_config_params = {
                    "audio_encoding": texttospeech.AudioEncoding.LINEAR16,
                    "sample_rate_hertz": sample_rate,
                    "speaking_rate": self.speaking_rate,
                    "volume_gain_db": 0.0  # No volume gain - use natural Chirp3 HD levels
                    # Removed effects_profile_id to preserve natural Chirp3 HD characteristics
                }

                # Only add pitch for non-Chirp3 voices (Chirp3 HD doesn't support pitch adjustment)
                if "Chirp3" not in self.voice_name:
                    audio_config_params["pitch"] = self.pitch

                audio_config = texttospeech.AudioConfig(**audio_config_params)

                # Perform the text-to-speech request
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )

                # Convert audio content to numpy array
                audio_data = np.frombuffer(response.audio_content, dtype=np.int16)

                # Normalize to float32 in range [-1, 1] - preserve natural Chirp3 HD dynamics
                chunk_waveform = audio_data.astype(np.float32) / 32768.0

                all_audio_chunks.append(chunk_waveform)

            # Combine all chunks
            if len(all_audio_chunks) > 1:
                # Add small silence between chunks (100ms)
                silence_duration = int(sample_rate * 0.1)
                silence = np.zeros(silence_duration, dtype=np.float32)

                waveform_parts = []
                for chunk in all_audio_chunks:
                    waveform_parts.append(chunk)
                    waveform_parts.append(silence)

                # Remove last silence
                waveform_parts = waveform_parts[:-1]

                waveform = np.concatenate(waveform_parts)
            else:
                waveform = all_audio_chunks[0]

            # No peak normalization - preserve natural Chirp3 HD voice characteristics
            # The voice is already optimized by Google's Chirp3 HD processing

            print(f"✅ Speech synthesis complete!")
            print(f"   Duration: {len(waveform) / sample_rate:.2f}s")
            print(f"   Sample rate: {sample_rate} Hz")
            print(f"   Voice: {self.voice_name} ({self.voice_type})")

            # Save if output path provided
            if output_path:
                save_audio(output_path, waveform, sample_rate)

            return waveform

        except Exception as e:
            print(f"❌ Error during speech synthesis: {e}")
            import traceback
            traceback.print_exc()
            return None

    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        sample_rate: int = 24000
    ) -> bool:
        """
        Synthesize speech and save to file

        Args:
            text: Tamil text to synthesize
            output_path: Path to save audio file
            sample_rate: Output sample rate

        Returns:
            True if successful
        """
        try:
            waveform = self.synthesize(text, output_path, sample_rate)
            return waveform is not None
        except Exception as e:
            print(f"❌ Error synthesizing to file: {e}")
            return False

    def synthesize_batch(
        self,
        texts: list,
        output_dir: Union[str, Path],
        sample_rate: int = 24000
    ) -> list:
        """
        Synthesize multiple texts

        Args:
            texts: List of Tamil texts
            output_dir: Directory to save audio files
            sample_rate: Output sample rate

        Returns:
            List of output file paths
        """
        output_paths = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, text in enumerate(texts):
            output_path = output_dir / f"speech_{i:03d}.wav"
            if self.synthesize_to_file(text, output_path, sample_rate):
                output_paths.append(str(output_path))

        return output_paths

    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.is_loaded

    def set_speaking_rate(self, rate: float):
        """
        Set speaking rate

        Args:
            rate: Speaking rate (0.25 to 4.0, default 1.0)
        """
        self.speaking_rate = max(0.25, min(4.0, rate))
        print(f"🔧 Speaking rate set to: {self.speaking_rate}x")

    def set_pitch(self, pitch: float):
        """
        Set voice pitch

        Args:
            pitch: Pitch in semitones (-20.0 to 20.0, default 0.0)
        """
        self.pitch = max(-20.0, min(20.0, pitch))
        print(f"🔧 Voice pitch set to: {self.pitch:+.1f} semitones")


class GoogleTTS:
    """
    Google Text-to-Speech (gTTS) fallback engine

    Features:
    - Free, no API keys required
    - Internet connection required
    - Female voice with audio enhancements
    - Good quality for basic use cases
    """

    def __init__(
        self,
        lang: str = "ta",
        slow: bool = False,
        tld: str = "co.in"
    ):
        """
        Initialize gTTS engine

        Args:
            lang: Language code (ta for Tamil)
            slow: Speak slowly for better clarity
            tld: Top-level domain for accent (co.in for Indian accent)
        """
        self.lang = lang
        self.slow = slow
        self.tld = tld
        self.is_loaded = True

    def load_model(self) -> bool:
        """
        Load the TTS model (not needed for gTTS)

        Returns:
            True (always ready)
        """
        try:
            from gtts import gTTS
            print("✅ Google TTS (gTTS) ready!")
            print("   Note: Using fallback gTTS (free, internet-required)")
            return True
        except ImportError:
            print("❌ gtts not installed. Install with: pip install gtts")
            return False

    def synthesize(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        sample_rate: int = 24000
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech from text

        Args:
            text: Tamil text to synthesize
            output_path: Optional path to save audio file
            sample_rate: Output sample rate

        Returns:
            Audio data as numpy array
        """
        if not self.is_loaded:
            raise RuntimeError("TTS not ready. Call load_model() first.")

        try:
            from gtts import gTTS
            from pydub import AudioSegment

            print(f"\n🔊 Synthesizing speech with gTTS...")
            print(f"   Text: {text[:100]}...")
            print(f"   Language: Tamil (Female Voice)")

            # Create gTTS object
            tts = gTTS(
                text=text,
                lang=self.lang,
                slow=self.slow,
                tld=self.tld
            )

            # Save to temporary buffer
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_fp)

            # Audio enhancements
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * 0.95)  # 5% slower
            })
            audio = audio.set_frame_rate(audio.frame_rate)
            audio = audio.high_pass_filter(80)
            audio = audio.low_pass_filter(8000)
            audio = audio.normalize()
            audio = audio.compress_dynamic_range(threshold=-20.0, ratio=3.0)

            # Set sample rate
            if audio.frame_rate != sample_rate:
                audio = audio.set_frame_rate(sample_rate)

            # Convert to mono
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Get raw audio data as numpy array
            samples = np.array(audio.get_array_of_samples())

            # Normalize to float32
            if audio.sample_width == 2:
                waveform = samples.astype(np.float32) / 32768.0
            else:
                waveform = samples.astype(np.float32) / (2 ** (8 * audio.sample_width - 1))

            print(f"✅ Speech synthesis complete!")
            print(f"   Duration: {len(waveform) / sample_rate:.2f}s")

            # Save if output path provided
            if output_path:
                save_audio(output_path, waveform, sample_rate)

            return waveform

        except Exception as e:
            print(f"❌ Error during speech synthesis: {e}")
            import traceback
            traceback.print_exc()
            return None

    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        sample_rate: int = 24000
    ) -> bool:
        """Synthesize speech and save to file"""
        try:
            waveform = self.synthesize(text, output_path, sample_rate)
            return waveform is not None
        except Exception as e:
            print(f"❌ Error synthesizing to file: {e}")
            return False

    def synthesize_batch(
        self,
        texts: list,
        output_dir: Union[str, Path],
        sample_rate: int = 24000
    ) -> list:
        """Synthesize multiple texts"""
        output_paths = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, text in enumerate(texts):
            output_path = output_dir / f"speech_{i:03d}.wav"
            if self.synthesize_to_file(text, output_path, sample_rate):
                output_paths.append(str(output_path))

        return output_paths

    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.is_loaded


# Global TTS instance
_tts_instance: Optional[Union[GoogleCloudTTS, GoogleTTS]] = None


def reset_tts_engine():
    """
    Reset the global TTS engine instance.
    Call this to force reinitialization with updated settings.
    """
    global _tts_instance
    _tts_instance = None
    print("🔄 TTS engine reset. Will reinitialize on next use.")


def get_tts_engine(force_fallback: bool = False) -> Union[GoogleCloudTTS, GoogleTTS]:
    """
    Get or create global TTS engine instance

    Args:
        force_fallback: If True, use gTTS regardless of settings

    Returns:
        TTS engine (Google Cloud TTS or gTTS fallback)
    """
    global _tts_instance

    if _tts_instance is None or force_fallback:
        if settings.USE_GOOGLE_CLOUD_TTS and not force_fallback:
            # Try Google Cloud TTS first with configured voice parameters
            _tts_instance = GoogleCloudTTS(
                voice_name=settings.TTS_MODEL_NAME,
                language_code="ta-IN",
                speaking_rate=settings.TTS_SPEAKING_RATE,  # Customizable speed (5% slower for elegance)
                pitch=settings.TTS_PITCH  # Customizable pitch (slightly lower for warmth)
            )

            if not _tts_instance.load_model():
                print("⚠️  Falling back to gTTS...")
                _tts_instance = GoogleTTS(
                    lang="ta",
                    slow=False,
                    tld="co.in"
                )
                _tts_instance.load_model()
        else:
            # Use gTTS directly
            _tts_instance = GoogleTTS(
                lang="ta",
                slow=False,
                tld="co.in"
            )
            _tts_instance.load_model()

    return _tts_instance


def initialize_tts() -> bool:
    """
    Initialize global TTS engine

    Returns:
        True if initialized successfully
    """
    tts = get_tts_engine()
    if not tts.is_model_loaded():
        return tts.load_model()
    return True


def synthesize_speech(
    text: str,
    output_path: Optional[Union[str, Path]] = None
) -> Optional[np.ndarray]:
    """
    Convenience function to synthesize speech with automatic fallback

    Args:
        text: Tamil text to synthesize
        output_path: Optional path to save audio

    Returns:
        Audio data as numpy array
    """
    tts = get_tts_engine()

    if not tts.is_model_loaded():
        if not tts.load_model():
            return None

    # Try synthesis
    result = tts.synthesize(text, output_path)

    # If Google Cloud TTS failed and we haven't tried fallback yet
    if result is None and isinstance(tts, GoogleCloudTTS):
        print("\n⚠️  Google Cloud TTS failed. Attempting gTTS fallback...")

        # Get gTTS engine
        global _tts_instance
        _tts_instance = None  # Reset global instance
        tts = get_tts_engine(force_fallback=True)

        # Retry with gTTS
        result = tts.synthesize(text, output_path)

    return result


if __name__ == "__main__":
    # Test TTS
    print("="*70)
    print("🧪 Testing Tamil Text-to-Speech")
    print("="*70)

    # Initialize TTS
    tts = get_tts_engine()

    print(f"\n📊 TTS Engine: {type(tts).__name__}")
    if isinstance(tts, GoogleCloudTTS):
        print(f"   Mode: Google Cloud TTS ({tts.voice_type})")
    else:
        print("   Mode: gTTS (Free Fallback)")

    if tts.load_model():
        print("\n" + "="*70)
        print("🧪 Test: Speech Synthesis")
        print("="*70)

        # Test Tamil texts
        test_texts = [
            "வணக்கம்! நான் தமிழ் பேசும் செயற்கை நுண்ணறிவு உதவியாளர்.",
            "செயற்கை நுண்ணறிவு என்பது கணினிகளை சிந்திக்க வைக்கும் தொழில்நுட்பம்.",
            "இன்று வானிலை எப்படி இருக்கிறது?",
        ]

        # Create output directory
        output_dir = Path("data/out")
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, text in enumerate(test_texts):
            print(f"\nTest {i+1}: {text}")
            output_path = output_dir / f"test_tts_{i+1}.wav"

            if tts.synthesize_to_file(text, output_path):
                print(f"✅ Saved to: {output_path}")
            else:
                print(f"❌ Failed to synthesize")

        print("\n" + "="*70)
        print("✅ TTS test complete!")
        print("="*70)
        print(f"\nCheck data/out/ directory for generated audio files")
        if isinstance(tts, GoogleCloudTTS):
            print(f"Voice: {tts.voice_name} ({tts.voice_type})")
        else:
            print("Voice: gTTS Tamil (Free, Internet-required)")
    else:
        print("\n❌ Failed to load TTS")
        print("\nSetup instructions:")
        print("1. For Google Cloud TTS:")
        print("   - Create Google Cloud project")
        print("   - Enable Text-to-Speech API")
        print("   - Create service account and download JSON key")
        print("   - Set GOOGLE_APPLICATION_CREDENTIALS in .env")
        print("2. For gTTS fallback:")
        print("   - pip install gtts pydub")
        print("   - Requires internet connection")
