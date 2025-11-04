"""
Speech-to-Text (STT) using Faster-Whisper for Tamil AI Voice Assistant

Provides Tamil speech recognition using the Faster-Whisper model.
Supports both file-based and streaming transcription.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings
from backend.speech.audio_utils import load_audio, trim_silence


class FasterWhisperSTT:
    """
    Faster-Whisper Speech-to-Text engine for Tamil
    
    Features:
    - Fast inference with CTranslate2
    - Tamil language support
    - Batch and streaming modes
    - Automatic language detection
    """
    
    def __init__(
        self,
        model_size: str = "large-v2",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "ta"
    ):
        """
        Initialize Faster-Whisper STT engine
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v2)
            device: Device to use (cpu, cuda)
            compute_type: Computation type (int8, float16, float32)
            language: Target language code (ta for Tamil)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.model = None
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """
        Load the Faster-Whisper model
        
        Returns:
            True if loaded successfully
        """
        try:
            from faster_whisper import WhisperModel
            
            print(f"🔧 Loading Faster-Whisper model...")
            print(f"   Model: {self.model_size}")
            print(f"   Device: {self.device}")
            print(f"   Compute type: {self.compute_type}")
            print(f"   Language: {self.language}")
            
            # Load model
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            
            self.is_loaded = True
            print("✅ Faster-Whisper model loaded successfully!")
            
            return True
            
        except ImportError:
            print("❌ faster-whisper not installed. Install with: pip install faster-whisper")
            return False
        except Exception as e:
            print(f"❌ Error loading Faster-Whisper model: {e}")
            return False
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe",
        beam_size: int = 5,
        best_of: int = 5,
        temperature: float = 0.0,
        vad_filter: bool = True,
        word_timestamps: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)
            task: Task type (transcribe or translate)
            beam_size: Beam size for decoding
            best_of: Number of candidates to consider
            temperature: Sampling temperature
            vad_filter: Use voice activity detection
            word_timestamps: Include word-level timestamps
            
        Returns:
            Dictionary with transcription results
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            print(f"\n🎤 Transcribing audio: {audio_path}")
            
            # Use specified language or default
            lang = language or self.language
            
            # Transcribe
            segments, info = self.model.transcribe(
                str(audio_path),
                language=lang,
                task=task,
                beam_size=beam_size,
                best_of=best_of,
                temperature=temperature,
                vad_filter=vad_filter,
                word_timestamps=word_timestamps
            )
            
            # Collect segments
            transcription_segments = []
            full_text = []
            
            for segment in segments:
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": getattr(segment, 'avg_logprob', 0.0)
                }
                
                if word_timestamps and hasattr(segment, 'words'):
                    segment_dict["words"] = [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        }
                        for word in segment.words
                    ]
                
                transcription_segments.append(segment_dict)
                full_text.append(segment.text.strip())
            
            # Combine results
            result = {
                "text": " ".join(full_text),
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": transcription_segments
            }
            
            print(f"✅ Transcription complete!")
            print(f"   Language: {result['language']} ({result['language_probability']:.2%})")
            print(f"   Duration: {result['duration']:.2f}s")
            print(f"   Text: {result['text'][:100]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ Error during transcription: {e}")
            return {
                "text": "",
                "error": str(e),
                "segments": []
            }
    
    def transcribe_audio_data(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None,
        save_refined_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio data (numpy array)

        Args:
            audio_data: Audio samples
            sample_rate: Sample rate in Hz
            language: Language code
            save_refined_path: Optional path to save noise-reduced audio for comparison

        Returns:
            Dictionary with transcription results
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Apply noise reduction preprocessing if enabled
            from backend.settings import settings
            if settings.ENABLE_NOISE_REDUCTION:
                from backend.speech.noise_reduction import reduce_noise
                print(f"🔊 Applying noise reduction (strength: {settings.NOISE_REDUCTION_STRENGTH})...")
                audio_data = reduce_noise(audio_data, sample_rate)
                print(f"✅ Noise reduction applied")

                # Save refined audio if path provided
                if save_refined_path:
                    from backend.speech.audio_utils import save_audio
                    save_audio(save_refined_path, audio_data, sample_rate)
                    print(f"💾 Saved noise-reduced audio to: {save_refined_path}")

            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            from backend.speech.audio_utils import save_audio
            save_audio(tmp_path, audio_data, sample_rate)

            # Transcribe
            result = self.transcribe(tmp_path, language=language)

            # Clean up
            os.unlink(tmp_path)

            return result

        except Exception as e:
            print(f"❌ Error transcribing audio data: {e}")
            return {
                "text": "",
                "error": str(e),
                "segments": []
            }
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.is_loaded


# Global STT instance
_stt_instance: Optional[FasterWhisperSTT] = None


def get_stt_engine() -> FasterWhisperSTT:
    """
    Get or create global STT engine instance
    
    Returns:
        FasterWhisperSTT instance
    """
    global _stt_instance
    
    if _stt_instance is None:
        _stt_instance = FasterWhisperSTT(
            model_size=settings.STT_MODEL_NAME,
            language="ta"
        )
    
    return _stt_instance


def initialize_stt() -> bool:
    """
    Initialize global STT engine
    
    Returns:
        True if initialized successfully
    """
    stt = get_stt_engine()
    if not stt.is_model_loaded():
        return stt.load_model()
    return True


def transcribe_audio(
    audio_path: Union[str, Path],
    language: str = "ta"
) -> str:
    """
    Convenience function to transcribe audio file
    
    Args:
        audio_path: Path to audio file
        language: Language code
        
    Returns:
        Transcribed text
    """
    stt = get_stt_engine()
    
    if not stt.is_model_loaded():
        if not stt.load_model():
            return ""
    
    result = stt.transcribe(audio_path, language=language)
    return result.get("text", "")


if __name__ == "__main__":
    # Test STT
    print("="*70)
    print("🧪 Testing Faster-Whisper STT")
    print("="*70)
    
    # Initialize STT
    stt = get_stt_engine()
    
    if stt.load_model():
        print("\n" + "="*70)
        print("🧪 Test: Audio Transcription")
        print("="*70)
        
        # Create test audio file
        from backend.speech.audio_utils import save_audio
        import numpy as np
        
        # Generate test audio (silence for now)
        sample_rate = 16000
        duration = 2.0
        test_audio = np.zeros(int(sample_rate * duration))
        
        test_path = "data/out/test_stt.wav"
        save_audio(test_path, test_audio, sample_rate)
        
        # Transcribe
        result = stt.transcribe(test_path)
        
        print(f"\nTranscription result:")
        print(f"  Text: {result.get('text', 'N/A')}")
        print(f"  Language: {result.get('language', 'N/A')}")
        print(f"  Duration: {result.get('duration', 0):.2f}s")
        
        print("\n" + "="*70)
        print("✅ STT test complete!")
        print("="*70)
        print("\nNote: For real testing, provide actual Tamil audio files")
    else:
        print("\n❌ Failed to load STT model")
        print("\nSetup instructions:")
        print("1. Install faster-whisper: pip install faster-whisper")
        print("2. Model will be downloaded automatically on first use")
