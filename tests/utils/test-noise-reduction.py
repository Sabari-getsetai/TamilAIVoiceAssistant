#!/usr/bin/env python3
"""
Test noise reduction preprocessing for Tamil AI Voice Assistant

This script tests the noise reduction feature by comparing STT transcription
quality with and without noise reduction on saved audio files.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def test_noise_reduction():
    """Test noise reduction with saved audio files"""
    print("=" * 70)
    print("🧪 Testing Noise Reduction for STT")
    print("=" * 70)

    # Check if we have saved audio files to test
    user_audio_dir = Path("data/out/user_audio")
    if not user_audio_dir.exists():
        print(f"\n❌ No saved audio files found in {user_audio_dir}")
        print("   Please record some audio first using the voice assistant")
        return False

    # Get the most recent audio file
    audio_files = sorted(user_audio_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not audio_files:
        print(f"\n❌ No .wav files found in {user_audio_dir}")
        print("   Please record some audio first using the voice assistant")
        return False

    test_file = audio_files[0]
    print(f"\n📁 Using most recent audio file: {test_file.name}")

    try:
        from backend.speech.audio_utils import load_audio
        from backend.speech.stt import FasterWhisperSTT
        from backend import settings

        # Load audio file
        audio_data, sample_rate = load_audio(str(test_file), sample_rate=16000)
        duration = len(audio_data) / sample_rate
        print(f"   Duration: {duration:.2f}s")
        print(f"   Sample rate: {sample_rate}Hz")

        # Initialize STT
        print(f"\n🔧 Initializing Faster-Whisper STT...")
        stt = FasterWhisperSTT()
        stt.load_model()

        # Test 1: WITHOUT noise reduction
        print("\n" + "=" * 70)
        print("Test 1: STT WITHOUT Noise Reduction")
        print("=" * 70)

        # Temporarily disable noise reduction
        original_setting = settings.settings.ENABLE_NOISE_REDUCTION
        settings.settings.ENABLE_NOISE_REDUCTION = False

        result_without = stt.transcribe_audio_data(audio_data, sample_rate, language="ta")
        text_without = result_without.get("text", "")
        confidence_without = result_without.get("language_probability", 0)

        print(f"📝 Transcription: {text_without}")
        print(f"🎯 Confidence: {confidence_without:.2%}")

        # Test 2: WITH noise reduction
        print("\n" + "=" * 70)
        print("Test 2: STT WITH Noise Reduction")
        print("=" * 70)

        settings.settings.ENABLE_NOISE_REDUCTION = True

        result_with = stt.transcribe_audio_data(audio_data, sample_rate, language="ta")
        text_with = result_with.get("text", "")
        confidence_with = result_with.get("language_probability", 0)

        print(f"📝 Transcription: {text_with}")
        print(f"🎯 Confidence: {confidence_with:.2%}")

        # Restore original setting
        settings.settings.ENABLE_NOISE_REDUCTION = original_setting

        # Comparison
        print("\n" + "=" * 70)
        print("📊 Comparison Results")
        print("=" * 70)
        print(f"Without noise reduction: {text_without}")
        print(f"With noise reduction:    {text_with}")
        print(f"\nConfidence change: {(confidence_with - confidence_without):.2%}")

        # Check if texts are different
        if text_without != text_with:
            print(f"\n⚠️  Transcriptions differ!")
            print(f"   This indicates noise reduction affected the result.")
            print(f"   Review both transcriptions to determine which is more accurate.")
        else:
            print(f"\n✅ Transcriptions are identical")
            print(f"   Noise reduction preserved the transcription while cleaning audio.")

        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)
        print(f"\nRecommendations:")
        print(f"- If transcription improved: Keep noise reduction enabled")
        print(f"- If transcription degraded: Try lower strength (0.4-0.5)")
        print(f"- If no change: Audio may already be clean")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_files():
    """Test noise reduction on multiple audio files"""
    print("=" * 70)
    print("🧪 Testing Noise Reduction on Multiple Files")
    print("=" * 70)

    user_audio_dir = Path("data/out/user_audio")
    audio_files = sorted(user_audio_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]

    if not audio_files:
        print(f"\n❌ No audio files found in {user_audio_dir}")
        return False

    print(f"\n📁 Found {len(audio_files)} audio files to test")

    from backend.speech.audio_utils import load_audio
    from backend.speech.stt import FasterWhisperSTT
    from backend import settings

    stt = FasterWhisperSTT()
    stt.load_model()

    results = []

    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n--- Testing file {i}/{len(audio_files)}: {audio_file.name} ---")

        audio_data, sample_rate = load_audio(str(audio_file), sample_rate=16000)

        # Test without noise reduction
        settings.settings.ENABLE_NOISE_REDUCTION = False
        result_without = stt.transcribe_audio_data(audio_data, sample_rate, language="ta")

        # Test with noise reduction
        settings.settings.ENABLE_NOISE_REDUCTION = True
        result_with = stt.transcribe_audio_data(audio_data, sample_rate, language="ta")

        results.append({
            "file": audio_file.name,
            "without": result_without.get("text", ""),
            "with": result_with.get("text", ""),
            "improvement": result_with.get("language_probability", 0) - result_without.get("language_probability", 0)
        })

        print(f"Without NR: {result_without.get('text', '')}")
        print(f"With NR:    {result_with.get('text', '')}")

    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary of All Tests")
    print("=" * 70)

    improved = sum(1 for r in results if r["improvement"] > 0)
    same = sum(1 for r in results if r["improvement"] == 0)
    degraded = sum(1 for r in results if r["improvement"] < 0)

    print(f"Improved:  {improved}/{len(results)} files")
    print(f"Same:      {same}/{len(results)} files")
    print(f"Degraded:  {degraded}/{len(results)} files")

    avg_improvement = sum(r["improvement"] for r in results) / len(results)
    print(f"\nAverage confidence improvement: {avg_improvement:.2%}")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test noise reduction for STT")
    parser.add_argument(
        "--multiple",
        action="store_true",
        help="Test multiple audio files instead of just the most recent"
    )

    args = parser.parse_args()

    if args.multiple:
        success = test_multiple_files()
    else:
        success = test_noise_reduction()

    sys.exit(0 if success else 1)
