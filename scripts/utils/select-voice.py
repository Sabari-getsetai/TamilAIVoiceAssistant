#!/usr/bin/env python3
"""
Voice Selection Tool for Tamil AI Voice Assistant

Listen to different voice samples and select your favorite!
"""

import os
from pathlib import Path

# Available high-quality Tamil voices
RECOMMENDED_VOICES = {
    "1": {"name": "ta-IN-Wavenet-C", "gender": "FEMALE", "quality": "WaveNet", "description": "WaveNet Female C - Natural, warm"},
    "2": {"name": "ta-IN-Chirp3-HD-Achernar", "gender": "FEMALE", "quality": "Chirp3-HD", "description": "Chirp3-HD Achernar - Latest AI, very natural"},
    "3": {"name": "ta-IN-Chirp3-HD-Aoede", "gender": "FEMALE", "quality": "Chirp3-HD", "description": "Chirp3-HD Aoede - Latest AI, expressive"},
    "4": {"name": "ta-IN-Chirp3-HD-Callirrhoe", "gender": "FEMALE", "quality": "Chirp3-HD", "description": "Chirp3-HD Callirrhoe - Latest AI, clear"},
    "5": {"name": "ta-IN-Chirp3-HD-Despina", "gender": "FEMALE", "quality": "Chirp3-HD", "description": "Chirp3-HD Despina - Latest AI, smooth"},
    "6": {"name": "ta-IN-Chirp3-HD-Gacrux", "gender": "FEMALE", "quality": "Chirp3-HD", "description": "Chirp3-HD Gacrux - Latest AI, professional"},
    "7": {"name": "ta-IN-Wavenet-A", "gender": "FEMALE", "quality": "WaveNet", "description": "WaveNet Female A - Classic, reliable"},
}

def print_header():
    print("="*70)
    print("🎤 TAMIL VOICE ASSISTANT - VOICE SELECTION")
    print("="*70)
    print()

def print_voice_options():
    print("Available Tamil Female Voices:")
    print()
    for key, voice in RECOMMENDED_VOICES.items():
        print(f"  [{key}] {voice['name']}")
        print(f"      {voice['description']}")
        print(f"      Quality: {voice['quality']} | Gender: {voice['gender']}")
        print()

def update_env_file(voice_name):
    """Update .env file with selected voice"""
    env_path = Path(".env")

    if not env_path.exists():
        print(f"❌ .env file not found at: {env_path}")
        return False

    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update TTS_MODEL_NAME
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('TTS_MODEL_NAME='):
            lines[i] = f'TTS_MODEL_NAME={voice_name}\n'
            updated = True
            break

    if not updated:
        # Add if not found
        lines.append(f'\nTTS_MODEL_NAME={voice_name}\n')

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)

    return True

def test_voice(voice_name):
    """Test the selected voice"""
    print(f"\n🔊 Testing voice: {voice_name}")
    print("-" * 70)

    import subprocess

    test_script = """
from backend.speech.tts import GoogleCloudTTS
from pathlib import Path

text = 'வணக்கம்! நான் உங்கள் தமிழ் செயற்கை நுண்ணறிவு உதவியாளர். உங்களுக்கு எப்படி உதவ முடியும்?'

tts = GoogleCloudTTS(voice_name='{}', language_code='ta-IN')
if tts.load_model():
    output_path = Path('data/out/selected_voice_test.wav')
    result = tts.synthesize(text, output_path=output_path)

    if result is not None:
        print(f'✅ Voice test successful!')
        print(f'Audio saved to: {{output_path}}')
        print(f'Duration: {{len(result) / 24000:.2f}}s')
    else:
        print('❌ Voice test failed')
else:
    print('❌ Failed to load TTS model')
""".format(voice_name)

    result = subprocess.run(
        ["python", "-c", test_script],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        return False
    return True

def main():
    print_header()

    # Check if voice comparison files exist
    comparison_dir = Path("data/out/voice_comparison")
    if comparison_dir.exists() and any(comparison_dir.glob("*.wav")):
        print("📁 Voice comparison samples available:")
        print(f"   {comparison_dir}")
        print()
        print("   Listen to these files to compare voices:")
        for wav_file in sorted(comparison_dir.glob("*.wav")):
            print(f"   - {wav_file.name}")
        print()

    print_voice_options()

    print("="*70)
    print()

    # Get user selection
    choice = input("Select a voice (1-7) or 'q' to quit: ").strip()

    if choice.lower() == 'q':
        print("\nExiting without changes.")
        return

    if choice not in RECOMMENDED_VOICES:
        print(f"\n❌ Invalid choice: {choice}")
        print("Please run again and select 1-7")
        return

    selected_voice = RECOMMENDED_VOICES[choice]
    voice_name = selected_voice["name"]

    print(f"\n✅ Selected: {voice_name}")
    print(f"   {selected_voice['description']}")
    print()

    # Confirm
    confirm = input(f"Update .env to use this voice? (y/n): ").strip().lower()

    if confirm != 'y':
        print("\nCancelled. No changes made.")
        return

    # Update .env
    if update_env_file(voice_name):
        print(f"\n✅ Updated .env file:")
        print(f"   TTS_MODEL_NAME={voice_name}")
        print()

        # Ask if user wants to test
        test = input("Test this voice now? (y/n): ").strip().lower()

        if test == 'y':
            if test_voice(voice_name):
                print("\n" + "="*70)
                print("✅ Voice selection complete!")
                print("="*70)
                print(f"\nYour assistant will now use: {voice_name}")
                print("Restart your application to use the new voice.")
            else:
                print("\n⚠️  Voice test encountered errors. Check the output above.")
        else:
            print("\n✅ Configuration updated!")
            print("Restart your application to use the new voice.")
    else:
        print("\n❌ Failed to update .env file")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
