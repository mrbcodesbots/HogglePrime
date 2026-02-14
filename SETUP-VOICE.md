# Hoggle Voice Setup Guide

**Goal:** Get Hoggle talking and listening on the school PC.

---

## What You'll Have When Done

- Press a foot pedal (or keyboard key) → talk to Hoggle
- Hoggle transcribes your speech (Whisper), thinks (n8n → Gemini), and speaks back (Chatterbox voice clone)
- Full round-trip target: under 3 seconds

---

## Step 1: Check CUDA (you probably already have it)

Since you have an RTX 4090 and Ollama running, CUDA is likely already installed.

**Check in PowerShell:**
```powershell
nvcc --version
```

If you see version info (like `release 12.x`), skip to Step 2.

If not found, download CUDA Toolkit 12.x from:
- https://developer.nvidia.com/cuda-downloads
- Select: Windows → x86_64 → 11 → exe (local)
- Run installer with default options

**Also check cuDNN:**
- Download from https://developer.nvidia.com/cudnn-downloads (needs NVIDIA account)
- Extract the zip
- Copy the `bin/`, `include/`, `lib/` folders into your CUDA install directory
  (usually `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\`)

---

## Step 2: Install Python 3.12

**Important:** You need Python 3.12 specifically. Python 3.14 and 3.13 won't work with Chatterbox.

1. Download Python 3.12 from https://www.python.org/downloads/release/python-3129/
2. Scroll down to "Files" and download the **Windows installer (64-bit)**
3. Run installer — check "Add Python to PATH"
4. Verify in PowerShell: `py -3.12 --version`

**If PowerShell blocks scripts (venv won't activate):**
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## Step 3: Create Virtual Environment & Install Dependencies

Open PowerShell and run each block in order:

```powershell
cd C:\Users\jason\Documents\HogglePrimeHome

# Create venv with Python 3.12
py -3.12 -m venv venv-voice
.\venv-voice\Scripts\activate
python -m pip install --upgrade pip
```

```powershell
# Install PyTorch with CUDA 12.1 support
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

```powershell
# Install Chatterbox TTS (--no-deps to bypass strict version pins)
pip install chatterbox-tts --no-deps
```

```powershell
# Install Chatterbox dependencies manually
pip install soundfile tokenizers conformer einops
pip install librosa==0.11.0 omegaconf safetensors==0.5.3 transformers==4.46.3 diffusers==0.29.0 pyloudnorm resemble-perth==1.0.1 s3tokenizer pykakasi==2.3.0
```

```powershell
# Install remaining voice pipeline deps
pip install faster-whisper sounddevice keyboard requests numpy
```

**Test it works:**
```powershell
python -c "from chatterbox.tts import ChatterboxTTS; print('Chatterbox OK')"
python -c "from faster_whisper import WhisperModel; print('faster-whisper OK')"
python -c "import sounddevice; print('sounddevice OK')"
```

---

## Step 4: Record Hoggle's Reference Voice

Chatterbox clones a voice from a short audio sample. You need a 10-15 second clip.

1. Record yourself doing Hoggle's voice (any words — it clones the *sound*, not the words)
2. Save as WAV or MP3
3. Put it at: `config\voice\hoggle-reference.mp3` (or .wav)
4. Update `config\voice\voice-config.json` if you used a different filename

**Test voice cloning:**
```powershell
python scripts\test_voice_clone.py config\voice\hoggle-reference.mp3
```
This generates 5 test phrases in `tools\voice_tests\`. Listen and make sure you like it!

---

## Step 5: Test Each Part Individually

Make sure you're in the virtual environment:
```powershell
cd C:\Users\jason\Documents\HogglePrimeHome
.\venv-voice\Scripts\activate
```

### Test audio devices
```powershell
python scripts\voice_pipeline.py --list-audio
```
This shows your microphone and speakers. Make sure the right ones are default.

### Test TTS only (Chatterbox speaks test phrases in Hoggle's cloned voice)
```powershell
python scripts\voice_pipeline.py --test-tts
```

### Test STT only (Whisper listens to you)
```powershell
python scripts\voice_pipeline.py --test-stt
```
First run downloads the Whisper model (~1.5 GB) - this is a one-time thing.
Press and hold SCROLL LOCK (or your configured PTT key), speak, release.

### Test type mode (type text, hear Hoggle speak)
```powershell
python scripts\voice_pipeline.py --type
```
This skips the microphone - you type messages and Hoggle speaks the response.
Great for testing TTS + n8n together without needing a mic.

---

## Step 6: Full Voice Pipeline

Once all individual tests work:

```powershell
python scripts\voice_pipeline.py
```

Press and hold your PTT key, speak, release. Hoggle listens, thinks, and speaks back.

---

## Changing the PTT Key

Edit `config\voice\voice-config.json` and change `ptt_key`:

| Key Name | When to Use |
|---|---|
| `scroll lock` | USB foot pedal (most pedals map to this) |
| `f13` | Some foot pedals use F13-F24 |
| `right ctrl` | Keyboard alternative |
| `space` | Quick testing (but blocks typing) |

If your foot pedal maps to a different key, run this to find out:
```powershell
python -c "import keyboard; print('Press the pedal...'); e = keyboard.read_event(); print(f'Key: {e.name}')"
```

---

## Troubleshooting

### "CUDA not available" / Whisper runs on CPU
- Make sure CUDA Toolkit 12.x is installed: `nvcc --version`
- Make sure cuDNN 9.x files are in the CUDA directory
- Reinstall PyTorch: `pip install --force-reinstall torch torchaudio --index-url https://download.pytorch.org/whl/cu121`

### Chatterbox import errors
- Make sure you used `--no-deps` when installing chatterbox-tts
- Make sure all manual deps were installed (Step 3)
- Check Python version: must be 3.12 (`python --version`)

### Response takes too long (>3 seconds)
- STT slow? Switch Whisper to `medium` model in config (less accurate but faster)
- TTS slow? Chatterbox on a 4090 should be fast (~1-2 seconds per phrase)
- LLM slow? Check if n8n/Gemini is responding quickly with curl first

### Microphone not picking up audio
- Run `python scripts\voice_pipeline.py --list-audio` to check devices
- Make sure the right mic is set as Windows default
- Try a different `ptt_key` in case the current one isn't being detected

### PowerShell won't activate venv
- Run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

---

## File Locations Reference

```
HogglePrimeHome\
├── config\voice\voice-config.json       ← All voice settings
├── config\voice\hoggle-reference.mp3    ← Hoggle's voice sample for cloning
├── scripts\voice_pipeline.py            ← The main pipeline script
├── scripts\test_chatterbox.py           ← Test Chatterbox base voice
├── scripts\test_voice_clone.py          ← Test voice cloning with reference
├── requirements-voice.txt               ← Python dependencies + install order
├── tools\voice_tests\                   ← Generated test audio files
└── venv-voice\                          ← Python virtual environment
```
