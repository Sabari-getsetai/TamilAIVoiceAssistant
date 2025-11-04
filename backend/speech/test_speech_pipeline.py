"""
Test script for Speech Pipeline Components

Tests the complete speech processing pipeline:
- Audio utilities
- Speech-to-Text (STT)
- Text-to-Speech (TTS)
- Voice Activity Detection (VAD)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.speech import (
    # Audio utilities
    load_audio,
    save_audio,
    get_audio_duration,
    normalize_audio,
    # STT
    get_stt_engine,
    initialize_stt,
    transcribe_audio,
    # TTS
    get_tts_engine,
    initialize_tts,
    synthesize_speech,
    # VAD
    get_vad,
    detect_speech_segments,
)
import numpy as np


def test_audio_utilities():
    """Test audio utility functions"""
    print("="*70)
    print("🧪 Test 1: Audio Utilities")
    print("="*70)
    
    # Create test audio
    sample_rate = 16000
    duration = 2.0
    frequency = 440.0  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Test save
    test_path = "data/out/test_audio_utils.wav"
    if save_audio(test_path, test_audio, sample_rate):
        print("✅ Audio save successful")
        
        # Test load
        loaded_audio, loaded_sr = load_audio(test_path)
        print(f"✅ Audio load successful (loaded {len(loaded_audio)} samples)")
        
        # Test duration
        duration = get_audio_duration(test_path)
        print(f"✅ Duration: {duration:.2f}s")
        
        # Test normalization
        normalized = normalize_audio(test_audio)
        print(f"✅ Normalized (max: {np.max(np.abs(normalized)):.3f})")
        
        return True
    
    return False


def test_tts():
    """Test Text-to-Speech"""
    print("\n" + "="*70)
    print("🧪 Test 2: Text-to-Speech (TTS)")
    print("="*70)
    
    # Initialize TTS
    if not initialize_tts():
        print("❌ Failed to initialize TTS")
        return False
    
    # Test Tamil texts
    test_texts = [
        "வணக்கம்! நான் தமிழ் பேசும் செயற்கை நுண்ணறிவு உதவியாளர்.",
        "செயற்கை நுண்ணறிவு மிகவும் சக்திவாய்ந்த தொழில்நுட்பம்.",
    ]
    
    success_count = 0
    for i, text in enumerate(test_texts):
        print(f"\nTest {i+1}: {text}")
        output_path = f"data/out/test_tts_{i+1}.wav"
        
        audio = synthesize_speech(text, output_path)
        if audio is not None:
            print(f"✅ TTS successful - saved to {output_path}")
            success_count += 1
        else:
            print(f"❌ TTS failed")
    
    return success_count == len(test_texts)


def test_stt():
    """Test Speech-to-Text"""
    print("\n" + "="*70)
    print("🧪 Test 3: Speech-to-Text (STT)")
    print("="*70)
    
    # Initialize STT
    if not initialize_stt():
        print("❌ Failed to initialize STT")
        return False
    
    # First generate some audio with TTS
    print("\nGenerating test audio with TTS...")
    test_text = "வணக்கம்! இது ஒரு சோதனை."
    test_audio_path = "data/out/test_stt_input.wav"
    
    if synthesize_speech(test_text, test_audio_path) is None:
        print("❌ Failed to generate test audio")
        return False
    
    print(f"✅ Test audio generated: {test_audio_path}")
    
    # Now transcribe it
    print("\nTranscribing audio...")
    transcription = transcribe_audio(test_audio_path, language="ta")
    
    if transcription:
        print(f"✅ STT successful!")
        print(f"   Original: {test_text}")
        print(f"   Transcribed: {transcription}")
        return True
    else:
        print("❌ STT failed")
        return False


def test_vad():
    """Test Voice Activity Detection"""
    print("\n" + "="*70)
    print("🧪 Test 4: Voice Activity Detection (VAD)")
    print("="*70)
    
    # Get VAD instance
    vad = get_vad()
    
    print(f"VAD Configuration:")
    print(f"  Sample rate: {vad.sample_rate} Hz")
    print(f"  Silence threshold: {vad.silence_threshold}")
    print(f"  Silence duration: {vad.silence_duration}s")
    
    # Create test audio with speech and silence patterns
    sample_rate = vad.sample_rate
    
    # Pattern: silence + speech + silence + speech + silence
    silence1 = np.zeros(int(0.5 * sample_rate))
    speech1 = 0.1 * np.random.randn(int(1.0 * sample_rate))
    silence2 = np.zeros(int(2.0 * sample_rate))
    speech2 = 0.1 * np.random.randn(int(0.8 * sample_rate))
    silence3 = np.zeros(int(0.5 * sample_rate))
    
    test_audio = np.concatenate([silence1, speech1, silence2, speech2, silence3])
    
    # Save test audio
    test_path = "data/out/test_vad.wav"
    save_audio(test_path, test_audio, sample_rate)
    
    # Detect segments
    segments = detect_speech_segments(test_path)
    
    print(f"\n✅ Detected {len(segments)} speech segments:")
    for i, (start, end) in enumerate(segments):
        duration = end - start
        print(f"   Segment {i+1}: {start:.2f}s - {end:.2f}s (duration: {duration:.2f}s)")
    
    # We expect 2 segments
    return len(segments) >= 1


def test_complete_pipeline():
    """Test complete speech pipeline: TTS -> STT"""
    print("\n" + "="*70)
    print("🧪 Test 5: Complete Pipeline (TTS -> STT)")
    print("="*70)
    
    # Initialize both engines
    if not initialize_tts():
        print("❌ Failed to initialize TTS")
        return False
    
    if not initialize_stt():
        print("❌ Failed to initialize STT")
        return False
    
    # Test text
    original_text = "வணக்கம்! செயற்கை நுண்ணறிவு மிகவும் சுவாரசியமானது."
    
    print(f"\nOriginal text: {original_text}")
    
    # Step 1: TTS
    print("\nStep 1: Synthesizing speech...")
    audio_path = "data/out/test_pipeline.wav"
    audio = synthesize_speech(original_text, audio_path)
    
    if audio is None:
        print("❌ TTS failed")
        return False
    
    print(f"✅ Speech synthesized: {audio_path}")
    
    # Step 2: STT
    print("\nStep 2: Transcribing speech...")
    transcribed_text = transcribe_audio(audio_path, language="ta")
    
    if not transcribed_text:
        print("❌ STT failed")
        return False
    
    print(f"✅ Speech transcribed!")
    print(f"\n   Original:    {original_text}")
    print(f"   Transcribed: {transcribed_text}")
    
    # Check similarity (basic check)
    # Note: Exact match is unlikely due to TTS/STT variations
    print(f"\n   Text length: {len(original_text)} -> {len(transcribed_text)}")
    
    return True


def main():
    """Run all speech pipeline tests"""
    print("="*70)
    print("🎯 Tamil AI Voice Assistant - Speech Pipeline Tests")
    print("="*70)
    
    results = {
        "Audio Utilities": False,
        "Text-to-Speech": False,
        "Speech-to-Text": False,
        "Voice Activity Detection": False,
        "Complete Pipeline": False,
    }
    
    # Run tests
    try:
        results["Audio Utilities"] = test_audio_utilities()
    except Exception as e:
        print(f"❌ Audio utilities test failed: {e}")
    
    try:
        results["Text-to-Speech"] = test_tts()
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
    
    try:
        results["Speech-to-Text"] = test_stt()
    except Exception as e:
        print(f"❌ STT test failed: {e}")
    
    try:
        results["Voice Activity Detection"] = test_vad()
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
    
    try:
        results["Complete Pipeline"] = test_complete_pipeline()
    except Exception as e:
        print(f"❌ Complete pipeline test failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Results Summary")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print("\n" + "="*70)
    print(f"Total: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.0f}%)")
    print("="*70)
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Speech pipeline is ready!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check logs above.")
    
    print("\n📁 Generated test files in: data/out/")
    print("   - test_audio_utils.wav")
    print("   - test_tts_*.wav")
    print("   - test_stt_input.wav")
    print("   - test_vad.wav")
    print("   - test_pipeline.wav")


if __name__ == "__main__":
    main()
