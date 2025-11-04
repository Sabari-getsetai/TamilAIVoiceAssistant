"""
Noise Reduction for Tamil AI Voice Assistant

Provides noise reduction preprocessing for improved STT transcription quality.
Uses spectral gating algorithm via noisereduce library.
"""

import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NoiseReducer:
    """
    Noise reduction using spectral gating for speech enhancement

    Features:
    - Stationary and non-stationary noise reduction
    - Configurable aggressiveness
    - Minimal speech distortion
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        noise_reduction_strength: float = 0.6,
        stationary_noise: bool = False,
        use_torch: bool = False
    ):
        """
        Initialize Noise Reducer

        Args:
            sample_rate: Audio sample rate in Hz
            noise_reduction_strength: Strength of reduction (0.0-1.0)
                - 0.3-0.5: Light reduction (preserves more speech nuances)
                - 0.5-0.7: Medium reduction (balanced, recommended)
                - 0.7-1.0: Aggressive reduction (may affect speech quality)
            stationary_noise: Use stationary noise reduction (faster, for constant noise)
            use_torch: Use PyTorch backend for GPU acceleration
        """
        self.sample_rate = sample_rate
        self.noise_reduction_strength = noise_reduction_strength
        self.stationary_noise = stationary_noise
        self.use_torch = use_torch

        # Lazy import noisereduce
        try:
            import noisereduce as nr
            self.nr = nr
            logger.info(f"✅ Noise reduction initialized (strength: {noise_reduction_strength})")
        except ImportError:
            logger.error("❌ noisereduce not installed. Install with: pip install noisereduce")
            self.nr = None

    def reduce_noise(
        self,
        audio_data: np.ndarray,
        noise_sample: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Apply noise reduction to audio

        Args:
            audio_data: Audio samples (float32, -1 to 1)
            noise_sample: Optional noise profile sample (first 0.5s of audio if None)

        Returns:
            Noise-reduced audio
        """
        if self.nr is None:
            logger.warning("⚠️ Noise reduction unavailable, returning original audio")
            return audio_data

        try:
            # Ensure audio is float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Skip if audio too short (< 0.5 seconds)
            min_samples = int(0.5 * self.sample_rate)
            if len(audio_data) < min_samples:
                logger.debug("⏭️ Audio too short for noise reduction, skipping")
                return audio_data

            # Apply noise reduction
            if self.stationary_noise:
                # Stationary noise reduction (faster)
                reduced = self.nr.reduce_noise(
                    y=audio_data,
                    sr=self.sample_rate,
                    stationary=True,
                    prop_decrease=self.noise_reduction_strength,
                    use_torch=self.use_torch
                )
            else:
                # Non-stationary noise reduction (better quality)
                reduced = self.nr.reduce_noise(
                    y=audio_data,
                    sr=self.sample_rate,
                    stationary=False,
                    prop_decrease=self.noise_reduction_strength,
                    use_torch=self.use_torch,
                    n_fft=512  # Optimized for speech (23ms at 22kHz, ~36ms at 16kHz)
                )

            # Log reduction metrics
            original_rms = np.sqrt(np.mean(audio_data ** 2))
            reduced_rms = np.sqrt(np.mean(reduced ** 2))
            reduction_db = 20 * np.log10(reduced_rms / (original_rms + 1e-10))

            logger.debug(f"🔊 Noise reduction applied: {reduction_db:.1f} dB change")

            return reduced

        except Exception as e:
            logger.error(f"❌ Error during noise reduction: {e}")
            return audio_data

    def reduce_noise_with_auto_profile(
        self,
        audio_data: np.ndarray,
        noise_duration_seconds: float = 0.5
    ) -> np.ndarray:
        """
        Reduce noise using automatic noise profile from beginning of audio

        Args:
            audio_data: Audio samples
            noise_duration_seconds: Duration of noise sample from start (seconds)

        Returns:
            Noise-reduced audio
        """
        if self.nr is None:
            return audio_data

        try:
            # Extract noise sample from beginning
            noise_samples = int(noise_duration_seconds * self.sample_rate)
            if len(audio_data) > noise_samples:
                noise_sample = audio_data[:noise_samples]
                return self.reduce_noise(audio_data, noise_sample)
            else:
                return self.reduce_noise(audio_data)

        except Exception as e:
            logger.error(f"❌ Error in auto-profile noise reduction: {e}")
            return audio_data


# Global noise reducer instance
_noise_reducer_instance: Optional[NoiseReducer] = None


def get_noise_reducer() -> NoiseReducer:
    """
    Get or create global noise reducer instance

    Returns:
        NoiseReducer instance
    """
    global _noise_reducer_instance

    if _noise_reducer_instance is None:
        from backend.settings import settings

        _noise_reducer_instance = NoiseReducer(
            sample_rate=settings.AUDIO_SAMPLE_RATE,
            noise_reduction_strength=settings.NOISE_REDUCTION_STRENGTH,
            stationary_noise=settings.NOISE_REDUCTION_STATIONARY,
            use_torch=settings.NOISE_REDUCTION_USE_TORCH
        )

    return _noise_reducer_instance


def reduce_noise(
    audio_data: np.ndarray,
    sample_rate: int = 16000
) -> np.ndarray:
    """
    Convenience function to reduce noise in audio

    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz

    Returns:
        Noise-reduced audio
    """
    reducer = get_noise_reducer()
    return reducer.reduce_noise(audio_data)
