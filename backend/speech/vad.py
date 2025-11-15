"""
Voice Activity Detection (VAD) for Tamil AI Voice Assistant

Provides real-time voice activity detection to determine when users are speaking.
Supports silence detection for natural conversation flow.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple, Union
import numpy as np
import time


from backend.settings import settings
from backend.speech.audio_utils import load_audio


class VoiceActivityDetector:
    """
    Voice Activity Detection for real-time conversation
    
    Features:
    - Real-time silence detection
    - Configurable thresholds
    - Energy-based and WebRTC VAD
    - Conversation flow management
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        min_speech_duration: float = 0.3
    ):
        """
        Initialize Voice Activity Detector
        
        Args:
            sample_rate: Audio sample rate in Hz
            frame_duration_ms: Frame duration in milliseconds
            silence_threshold: Energy threshold for silence detection
            silence_duration: Duration of silence to detect end of speech (seconds)
            min_speech_duration: Minimum speech duration to consider valid (seconds)
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        
        # Calculate frame size
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # State tracking
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.silence_start_time = None
        
        # WebRTC VAD (optional)
        self.webrtc_vad = None
        self._init_webrtc_vad()
        
    def _init_webrtc_vad(self):
        """Initialize WebRTC VAD if available"""
        try:
            import webrtcvad
            self.webrtc_vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3
            print("✅ WebRTC VAD initialized")
        except ImportError:
            print("⚠️  WebRTC VAD not available. Using energy-based VAD.")
            self.webrtc_vad = None
    
    def calculate_energy(self, audio_frame: np.ndarray) -> float:
        """
        Calculate energy of audio frame
        
        Args:
            audio_frame: Audio samples
            
        Returns:
            Energy value
        """
        if len(audio_frame) == 0:
            return 0.0
        
        # RMS energy
        energy = np.sqrt(np.mean(audio_frame ** 2))
        return energy
    
    def is_speech_webrtc(self, audio_frame: np.ndarray) -> bool:
        """
        Detect speech using WebRTC VAD
        
        Args:
            audio_frame: Audio samples (must be 16kHz, 16-bit)
            
        Returns:
            True if speech detected
        """
        if self.webrtc_vad is None:
            return False
        
        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio_frame * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            
            # WebRTC VAD requires specific frame sizes
            if len(audio_bytes) not in [320, 640, 960]:  # 10ms, 20ms, 30ms at 16kHz
                return False
            
            return self.webrtc_vad.is_speech(audio_bytes, self.sample_rate)
            
        except Exception as e:
            print(f"WebRTC VAD error: {e}")
            return False
    
    def is_speech_energy(self, audio_frame: np.ndarray) -> bool:
        """
        Detect speech using energy threshold
        
        Args:
            audio_frame: Audio samples
            
        Returns:
            True if speech detected
        """
        energy = self.calculate_energy(audio_frame)
        return energy > self.silence_threshold
    
    def process_frame(self, audio_frame: np.ndarray) -> dict:
        """
        Process audio frame and update VAD state
        
        Args:
            audio_frame: Audio samples
            
        Returns:
            Dictionary with VAD results
        """
        current_time = time.time()
        
        # Detect speech in frame
        if self.webrtc_vad:
            is_speech_frame = self.is_speech_webrtc(audio_frame)
        else:
            is_speech_frame = self.is_speech_energy(audio_frame)
        
        # Calculate energy for monitoring
        energy = self.calculate_energy(audio_frame)
        
        # State management
        speech_started = False
        speech_ended = False
        
        if is_speech_frame:
            # Speech detected
            if not self.is_speaking:
                # Speech just started
                self.is_speaking = True
                self.speech_start_time = current_time
                speech_started = True
                print(f"🎤 Speech started (energy: {energy:.4f})")
            
            self.last_speech_time = current_time
            self.silence_start_time = None
            
        else:
            # No speech detected
            if self.is_speaking:
                # We were speaking, now silence
                if self.silence_start_time is None:
                    self.silence_start_time = current_time
                
                # Check if silence duration exceeded
                silence_duration = current_time - self.silence_start_time
                if silence_duration >= self.silence_duration:
                    # Check minimum speech duration
                    if self.speech_start_time:
                        speech_duration = self.last_speech_time - self.speech_start_time
                        if speech_duration >= self.min_speech_duration:
                            # Valid speech ended
                            self.is_speaking = False
                            speech_ended = True
                            print(f"🔇 Speech ended (duration: {speech_duration:.2f}s)")
                        else:
                            # Too short, ignore
                            self.is_speaking = False
                            print(f"⚠️  Speech too short ({speech_duration:.2f}s), ignored")
                    else:
                        self.is_speaking = False
        
        return {
            "is_speech": is_speech_frame,
            "is_speaking": self.is_speaking,
            "speech_started": speech_started,
            "speech_ended": speech_ended,
            "energy": energy,
            "silence_duration": (current_time - self.silence_start_time) if self.silence_start_time else 0.0
        }
    
    def process_audio(self, audio_data: np.ndarray) -> List[dict]:
        """
        Process entire audio buffer
        
        Args:
            audio_data: Audio samples
            
        Returns:
            List of frame results
        """
        results = []
        
        # Process in frames
        for i in range(0, len(audio_data), self.frame_size):
            frame = audio_data[i:i + self.frame_size]
            
            # Pad frame if needed
            if len(frame) < self.frame_size:
                frame = np.pad(frame, (0, self.frame_size - len(frame)))
            
            result = self.process_frame(frame)
            results.append(result)
        
        return results
    
    def detect_speech_segments(
        self,
        audio_data: np.ndarray
    ) -> List[Tuple[float, float]]:
        """
        Detect speech segments in audio
        
        Args:
            audio_data: Audio samples
            
        Returns:
            List of (start_time, end_time) tuples in seconds
        """
        results = self.process_audio(audio_data)
        segments = []
        
        current_segment_start = None
        
        for i, result in enumerate(results):
            time_offset = i * self.frame_duration_ms / 1000.0
            
            if result["speech_started"]:
                current_segment_start = time_offset
            elif result["speech_ended"] and current_segment_start is not None:
                segments.append((current_segment_start, time_offset))
                current_segment_start = None
        
        # Handle case where speech continues to end
        if current_segment_start is not None:
            end_time = len(results) * self.frame_duration_ms / 1000.0
            segments.append((current_segment_start, end_time))
        
        return segments
    
    def reset(self):
        """Reset VAD state"""
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.silence_start_time = None


# Global VAD instance
_vad_instance: Optional[VoiceActivityDetector] = None


def get_vad() -> VoiceActivityDetector:
    """
    Get or create global VAD instance
    
    Returns:
        VoiceActivityDetector instance
    """
    global _vad_instance
    
    if _vad_instance is None:
        _vad_instance = VoiceActivityDetector(
            sample_rate=settings.AUDIO_SAMPLE_RATE,
            silence_threshold=settings.VAD_SILENCE_THRESHOLD,
            silence_duration=settings.VAD_SILENCE_DURATION
        )
    
    return _vad_instance


def detect_speech_segments(
    audio_path: Union[str, Path]
) -> List[Tuple[float, float]]:
    """
    Convenience function to detect speech segments in audio file
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        List of (start_time, end_time) tuples
    """
    vad = get_vad()
    
    # Load audio
    audio_data, sample_rate = load_audio(audio_path, sample_rate=vad.sample_rate)
    
    # Detect segments
    return vad.detect_speech_segments(audio_data)


if __name__ == "__main__":
    # Test VAD
    print("="*70)
    print("🧪 Testing Voice Activity Detection")
    print("="*70)
    
    # Initialize VAD
    vad = get_vad()
    
    print(f"VAD Configuration:")
    print(f"  Sample rate: {vad.sample_rate} Hz")
    print(f"  Frame size: {vad.frame_size} samples")
    print(f"  Silence threshold: {vad.silence_threshold}")
    print(f"  Silence duration: {vad.silence_duration}s")
    print(f"  WebRTC VAD: {'Available' if vad.webrtc_vad else 'Not available'}")
    
    # Create test audio with speech and silence
    print("\n" + "="*70)
    print("🧪 Test: Speech Segment Detection")
    print("="*70)
    
    # Generate test audio: silence + speech + silence + speech + silence
    sample_rate = vad.sample_rate
    
    # Create segments
    silence1 = np.zeros(int(0.5 * sample_rate))  # 0.5s silence
    speech1 = 0.1 * np.random.randn(int(1.0 * sample_rate))  # 1.0s speech
    silence2 = np.zeros(int(2.0 * sample_rate))  # 2.0s silence (should trigger end)
    speech2 = 0.1 * np.random.randn(int(0.8 * sample_rate))  # 0.8s speech
    silence3 = np.zeros(int(0.5 * sample_rate))  # 0.5s silence
    
    test_audio = np.concatenate([silence1, speech1, silence2, speech2, silence3])
    
    # Save test audio
    from backend.speech.audio_utils import save_audio
    test_path = "data/out/test_vad.wav"
    save_audio(test_path, test_audio, sample_rate)
    
    # Detect segments
    segments = vad.detect_speech_segments(test_audio)
    
    print(f"\nDetected {len(segments)} speech segments:")
    for i, (start, end) in enumerate(segments):
        duration = end - start
        print(f"  Segment {i+1}: {start:.2f}s - {end:.2f}s (duration: {duration:.2f}s)")
    
    print("\n" + "="*70)
    print("✅ VAD test complete!")
    print("="*70)
    print(f"Test audio saved to: {test_path}")
