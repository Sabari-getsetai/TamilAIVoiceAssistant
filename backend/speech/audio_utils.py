"""
Audio processing utilities for Tamil AI Voice Assistant

Provides common audio operations:
- Loading and saving audio files
- Format conversion
- Audio normalization
- Duration calculation
"""

import os
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union
import soundfile as sf
import librosa


def load_audio(
    audio_path: Union[str, Path],
    sample_rate: Optional[int] = None,
    mono: bool = True
) -> Tuple[np.ndarray, int]:
    """
    Load audio file and optionally resample
    
    Args:
        audio_path: Path to audio file
        sample_rate: Target sample rate (None = keep original)
        mono: Convert to mono if True
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    try:
        # Load audio file
        audio, sr = librosa.load(
            audio_path,
            sr=sample_rate,
            mono=mono
        )
        
        print(f"✅ Loaded audio: {audio_path}")
        print(f"   Sample rate: {sr} Hz")
        print(f"   Duration: {len(audio) / sr:.2f} seconds")
        print(f"   Channels: {'Mono' if mono else 'Stereo'}")
        
        return audio, sr
        
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        raise


def save_audio(
    audio_path: Union[str, Path],
    audio_data: np.ndarray,
    sample_rate: int,
    format: str = "WAV"
) -> bool:
    """
    Save audio data to file
    
    Args:
        audio_path: Output file path
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        format: Audio format (WAV, FLAC, etc.)
        
    Returns:
        True if successful
    """
    try:
        # Ensure output directory exists
        output_dir = Path(audio_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save audio file
        sf.write(
            audio_path,
            audio_data,
            sample_rate,
            format=format
        )
        
        print(f"✅ Saved audio: {audio_path}")
        print(f"   Sample rate: {sample_rate} Hz")
        print(f"   Duration: {len(audio_data) / sample_rate:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving audio: {e}")
        return False


def convert_audio_format(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    target_sr: int = 16000,
    target_format: str = "WAV"
) -> bool:
    """
    Convert audio file to different format/sample rate
    
    Args:
        input_path: Input audio file
        output_path: Output audio file
        target_sr: Target sample rate
        target_format: Target format
        
    Returns:
        True if successful
    """
    try:
        # Load and resample
        audio, sr = load_audio(input_path, sample_rate=target_sr)
        
        # Save in new format
        return save_audio(output_path, audio, target_sr, format=target_format)
        
    except Exception as e:
        print(f"❌ Error converting audio: {e}")
        return False


def get_audio_duration(audio_path: Union[str, Path]) -> float:
    """
    Get duration of audio file in seconds
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        duration = librosa.get_duration(path=audio_path)
        return duration
        
    except Exception as e:
        print(f"❌ Error getting audio duration: {e}")
        return 0.0


def normalize_audio(
    audio_data: np.ndarray,
    target_level: float = -20.0
) -> np.ndarray:
    """
    Normalize audio to target dB level
    
    Args:
        audio_data: Audio samples
        target_level: Target level in dB
        
    Returns:
        Normalized audio
    """
    try:
        # Calculate current RMS level
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        if rms == 0:
            return audio_data
        
        # Calculate current level in dB
        current_db = 20 * np.log10(rms)
        
        # Calculate gain needed
        gain_db = target_level - current_db
        gain_linear = 10 ** (gain_db / 20)
        
        # Apply gain
        normalized = audio_data * gain_linear
        
        # Clip to prevent distortion
        normalized = np.clip(normalized, -1.0, 1.0)
        
        return normalized
        
    except Exception as e:
        print(f"❌ Error normalizing audio: {e}")
        return audio_data


def trim_silence(
    audio_data: np.ndarray,
    sample_rate: int,
    threshold_db: float = -40.0,
    frame_length: int = 2048,
    hop_length: int = 512
) -> np.ndarray:
    """
    Trim silence from beginning and end of audio
    
    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        threshold_db: Silence threshold in dB
        frame_length: Frame length for analysis
        hop_length: Hop length for analysis
        
    Returns:
        Trimmed audio
    """
    try:
        # Trim silence
        trimmed, _ = librosa.effects.trim(
            audio_data,
            top_db=-threshold_db,
            frame_length=frame_length,
            hop_length=hop_length
        )
        
        return trimmed
        
    except Exception as e:
        print(f"❌ Error trimming silence: {e}")
        return audio_data


def split_audio_chunks(
    audio_data: np.ndarray,
    sample_rate: int,
    chunk_duration: float = 30.0
) -> list:
    """
    Split audio into fixed-duration chunks
    
    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        chunk_duration: Chunk duration in seconds
        
    Returns:
        List of audio chunks
    """
    try:
        chunk_samples = int(chunk_duration * sample_rate)
        chunks = []
        
        for i in range(0, len(audio_data), chunk_samples):
            chunk = audio_data[i:i + chunk_samples]
            if len(chunk) > 0:
                chunks.append(chunk)
        
        print(f"✅ Split audio into {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        print(f"❌ Error splitting audio: {e}")
        return [audio_data]


def calculate_audio_features(
    audio_data: np.ndarray,
    sample_rate: int
) -> dict:
    """
    Calculate basic audio features
    
    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary of audio features
    """
    try:
        features = {
            "duration": len(audio_data) / sample_rate,
            "sample_rate": sample_rate,
            "num_samples": len(audio_data),
            "rms_energy": float(np.sqrt(np.mean(audio_data ** 2))),
            "max_amplitude": float(np.max(np.abs(audio_data))),
            "zero_crossing_rate": float(np.mean(librosa.zero_crossings(audio_data))),
        }
        
        return features
        
    except Exception as e:
        print(f"❌ Error calculating features: {e}")
        return {}


if __name__ == "__main__":
    # Test audio utilities
    print("="*70)
    print("🧪 Testing Audio Utilities")
    print("="*70)
    
    # Create test audio (1 second sine wave at 440 Hz)
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_audio = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Test save
    test_path = "data/out/test_audio.wav"
    if save_audio(test_path, test_audio, sample_rate):
        print("\n✅ Audio save test passed")
        
        # Test load
        loaded_audio, loaded_sr = load_audio(test_path)
        print("✅ Audio load test passed")
        
        # Test duration
        duration = get_audio_duration(test_path)
        print(f"✅ Duration: {duration:.2f} seconds")
        
        # Test normalization
        normalized = normalize_audio(test_audio)
        print(f"✅ Normalized audio (max: {np.max(np.abs(normalized)):.3f})")
        
        # Test features
        features = calculate_audio_features(test_audio, sample_rate)
        print(f"✅ Audio features: {features}")
        
        print("\n" + "="*70)
        print("✅ All audio utility tests passed!")
        print("="*70)
