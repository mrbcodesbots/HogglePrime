"""
Quick test: Chatterbox TTS for Hoggle's voice
Run: python scripts/test_chatterbox.py

First run downloads the model (~1.5 GB). After that it's fast.
"""
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent

print("Loading Chatterbox model (first run downloads ~1.5 GB)...")
model = ChatterboxTTS.from_pretrained(device="cuda")
print("Model loaded!")

# Test phrases that show Hoggle's personality range
test_lines = [
    "Hey hey! What's oinking? I'm Hoggle, Mr. B's teaching assistant!",
    "Nice try, but I can't write that paragraph for you! What's your gut say?",
    "Welcome to Multimedia Heroes! Ready to earn some MP today?",
    "FINE. I'll just go reorganize Level 4. ENDLESS yellow wallpaper.",
]

output_dir = PROJECT_DIR / "tools" / "voice_tests"
output_dir.mkdir(parents=True, exist_ok=True)

for i, line in enumerate(test_lines):
    print(f"\nGenerating: \"{line}\"")
    wav = model.generate(line)
    out_path = str(output_dir / f"hoggle_test_{i+1}.wav")
    ta.save(out_path, wav, model.sr)
    print(f"  Saved: {out_path}")

print(f"\nDone! Listen to the files in: {output_dir}")
print("If you like the base voice, next step is voice cloning with YOUR recording.")
