"""
Test Chatterbox voice cloning for Hoggle.

Usage:
    python scripts/test_voice_clone.py config/voice/hoggle-reference.wav

Records a reference voice, then generates test phrases in that voice.
"""
import sys
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_voice_clone.py <path-to-voice-file>")
        print("")
        print("Example:")
        print("  python scripts/test_voice_clone.py config/voice/hoggle-reference.wav")
        print("")
        print("The voice file should be 10-15 seconds of clean speech (WAV or MP3).")
        sys.exit(1)

    voice_file = sys.argv[1]
    if not os.path.exists(voice_file):
        print(f"[ERROR] File not found: {voice_file}")
        sys.exit(1)

    print(f"[VOICE] Reference file: {voice_file}")
    print("[MODEL] Loading Chatterbox (first run downloads ~1.5 GB)...")

    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device="cuda")
    print("[MODEL] Loaded!")

    # Test phrases that show Hoggle's personality range
    test_lines = [
        "Hey hey! What's oinking? Ready to earn some MP today?",
        "Nice try, but I can't write that paragraph for you! What's your gut say?",
        "Oink-credible work! Mr. B is gonna be so proud of you!",
        "FINE. Banished again. The Backrooms don't even have WiFi.",
        "Let's work through this together. What have you tried so far?",
    ]

    output_dir = PROJECT_DIR / "tools" / "voice_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[OUTPUT] Saving to: {output_dir}\n")

    for i, line in enumerate(test_lines):
        print(f"  Generating ({i+1}/{len(test_lines)}): \"{line}\"")
        wav = model.generate(
            line,
            audio_prompt_path=voice_file,
        )
        out_path = str(output_dir / f"hoggle_cloned_{i+1}.wav")
        ta.save(out_path, wav, model.sr)
        print(f"  -> {out_path}\n")

    print("=" * 60)
    print(f"  Done! Listen to the {len(test_lines)} files in:")
    print(f"  {output_dir}")
    print("")
    print("  If you like the voice, it's ready for the live pipeline!")
    print("  The reference file will be used automatically.")
    print("=" * 60)


if __name__ == "__main__":
    main()
