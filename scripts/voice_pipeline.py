"""
Hoggle Voice Pipeline
=====================
Push-to-talk voice interface for Hoggle / Forte / any character.

Flow: Microphone → Whisper STT → n8n Crystal Loader → Gemini → TTS → Speaker

TTS Engines:
    - elevenlabs: Fast cloud TTS (~0.3-0.5s). Requires API key + voice_id in active-character.json
    - chatterbox: Free local TTS with voice cloning (~5-8s). Requires reference MP3.

ElevenLabs Extras (when using elevenlabs engine):
    - Sound Effects: Gemini can embed {{sfx: description}} tags to play AI-generated SFX
    - Music: Gemini can embed {{music: description | 30s}} tags to play AI-generated music
    - Audio expression tags: [laughs], [sighs], etc. (eleven_v3 model only)

Music Engines (for {{song}} tags):
    - elevenlabs: Cloud music generation via ElevenLabs Music API
    - acestep: Local music generation via ACE-Step 1.5 (voice cloning, ~3-5s on RTX 4090)
      Set music_engine in active-character.json. ACE-Step runs in Docker on port 7860.

SFX Engines (for {{sfx}} tags):
    - elevenlabs: Cloud SFX via ElevenLabs Sound Generation API
    - audiogen: Local SFX via Meta AudioGen (AudioCraft) in Docker on port 7861
      Set sfx_engine in active-character.json. See docker/README.md for setup.

Usage:
    python voice_pipeline.py              # Normal PTT mode
    python voice_pipeline.py --type       # Type mode (keyboard input, TTS output)
    python voice_pipeline.py --test-tts   # Test TTS only
    python voice_pipeline.py --test-stt   # Test Whisper STT only
    python voice_pipeline.py --test-sfx   # Test sound effects generation
    python voice_pipeline.py --test-music # Test music generation
    python voice_pipeline.py --list-audio # List audio devices

Requires:
    pip install -r requirements-voice.txt
    For Chatterbox: CUDA 12.x + cuDNN 9.x, reference voice file
    For ElevenLabs: API key from https://elevenlabs.io
"""

import argparse
import json
import os
import re
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_DIR / "config" / "voice" / "voice-config.json"
CHARACTER_PATH = PROJECT_DIR / "config" / "active-character.json"


def load_config():
    """Load voice configuration from JSON file."""
    if not CONFIG_PATH.exists():
        print(f"[ERROR] Config not found: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    # Load active character config (overrides voice reference, TTS engine, etc.)
    config["_active_character"] = "hoggle"
    config["_voice_override"] = None
    config["_tts_engine"] = "chatterbox"
    config["_elevenlabs_api_key"] = None
    config["_elevenlabs_voice_id"] = None
    if CHARACTER_PATH.exists():
        try:
            with open(CHARACTER_PATH, "r") as f:
                char_config = json.load(f)
            config["_active_character"] = char_config.get("character", "hoggle")
            config["_voice_override"] = char_config.get("voice_reference")
            config["_tts_engine"] = char_config.get("tts_engine", "chatterbox")
            config["_elevenlabs_api_key"] = char_config.get("elevenlabs_api_key")
            config["_elevenlabs_voice_id"] = char_config.get("elevenlabs_voice_id")
            config["_elevenlabs_voice_settings"] = char_config.get("elevenlabs_voice_settings")
            config["_elevenlabs_model_id"] = char_config.get("elevenlabs_model_id")
            # Music & SFX settings (per-character)
            config["_music_style"] = char_config.get("music_style")
            config["_music_default_duration"] = char_config.get("music_default_duration", 10)
            config["_music_instrumental"] = char_config.get("music_instrumental", False)
            config["_music_intro_sfx"] = char_config.get("music_intro_sfx")
            config["_sfx_default_duration"] = char_config.get("sfx_default_duration")
            config["_sfx_prompt_influence"] = char_config.get("sfx_prompt_influence", 0.3)
            config["_music_engine"] = char_config.get("music_engine", "elevenlabs")
            config["_sfx_engine"] = char_config.get("sfx_engine", "elevenlabs")
        except (json.JSONDecodeError, KeyError):
            pass

    return config


# ---------------------------------------------------------------------------
# Whisper STT
# ---------------------------------------------------------------------------
class SpeechToText:
    def __init__(self, config):
        self.config = config["whisper"]
        self.model = None

    def initialize(self):
        """Load the Whisper model (takes a few seconds on first run)."""
        from faster_whisper import WhisperModel

        print(f"[STT] Loading Whisper model: {self.config['model']}...")
        print(f"[STT] Device: {self.config['device']}, Compute: {self.config['compute_type']}")

        self.model = WhisperModel(
            self.config["model"],
            device=self.config["device"],
            compute_type=self.config["compute_type"],
        )
        print("[STT] Model loaded and ready!")

    def transcribe(self, audio_path):
        """Transcribe an audio file to text."""
        start = time.time()
        segments, info = self.model.transcribe(
            audio_path,
            beam_size=self.config["beam_size"],
            language=self.config.get("language"),
            vad_filter=self.config.get("vad_filter", True),
        )

        text = " ".join(segment.text.strip() for segment in segments)
        elapsed = time.time() - start
        print(f"[STT] Transcribed in {elapsed:.2f}s: \"{text}\"")
        return text


# ---------------------------------------------------------------------------
# TTS Engine (ElevenLabs cloud or Chatterbox local)
# ---------------------------------------------------------------------------
class TextToSpeech:
    def __init__(self, config):
        self.character = config.get("_active_character", "hoggle")
        self.engine = config.get("_tts_engine", "chatterbox")

        # --- ElevenLabs settings ---
        self.elevenlabs_api_key = config.get("_elevenlabs_api_key")
        self.elevenlabs_voice_id = config.get("_elevenlabs_voice_id")
        el_config = config.get("elevenlabs", {})
        # Per-character model override (e.g. eleven_v3 for expression) > global default
        self.elevenlabs_model = config.get("_elevenlabs_model_id") or el_config.get("model_id", "eleven_turbo_v2_5")
        self.elevenlabs_format = el_config.get("output_format", "mp3_44100_128")

        # Voice settings: per-character override > global default
        default_vs = el_config.get("voice_settings", {})
        char_vs = config.get("_elevenlabs_voice_settings") or {}
        self.elevenlabs_voice_settings = {**default_vs, **char_vs}

        # --- Music & SFX settings (per-character) ---
        self.music_style = config.get("_music_style")
        self.music_default_duration = config.get("_music_default_duration", 10)
        self.music_instrumental = config.get("_music_instrumental", False)
        self.music_intro_sfx = config.get("_music_intro_sfx")
        self.sfx_default_duration = config.get("_sfx_default_duration")
        self.sfx_prompt_influence = config.get("_sfx_prompt_influence", 0.3)
        self.music_engine = config.get("_music_engine", "elevenlabs")

        self.sfx_engine = config.get("_sfx_engine", "elevenlabs")

        # --- ACE-Step settings (local music generation) ---
        self.acestep_config = config.get("acestep", {})

        # --- AudioGen settings (local SFX generation) ---
        self.audiogen_config = config.get("audiogen", {})

        # --- Chatterbox settings (fallback) ---
        self.chatterbox_config = config.get("chatterbox", {})
        self.model = None  # Chatterbox model (lazy loaded)

        # Voice reference (for Chatterbox)
        voice_override = config.get("_voice_override")
        ref_path = voice_override or self.chatterbox_config.get("reference_voice", "")
        if ref_path and not os.path.isabs(ref_path):
            ref_path = str(PROJECT_DIR / ref_path)
        self.reference_voice = ref_path

        # Validate ElevenLabs config — fall back to Chatterbox if missing
        if self.engine == "elevenlabs":
            if not self.elevenlabs_api_key or not self.elevenlabs_voice_id:
                print("[TTS] WARNING: ElevenLabs selected but missing api_key or voice_id")
                print("[TTS]          Set them in config/active-character.json")
                print("[TTS]          Falling back to Chatterbox")
                self.engine = "chatterbox"

        print(f"[TTS] Character: {self.character}")
        print(f"[TTS] Engine: {self.engine}")
        if self.engine == "elevenlabs":
            print(f"[TTS] Model: {self.elevenlabs_model}")
        if self.engine == "elevenlabs" and self.elevenlabs_voice_settings:
            vs = self.elevenlabs_voice_settings
            print(f"[TTS] Voice settings: stability={vs.get('stability')}, similarity={vs.get('similarity_boost')}")

        if self.engine == "chatterbox":
            print(f"[TTS] Reference voice: {self.reference_voice}")
            if self.reference_voice and not os.path.exists(self.reference_voice):
                print(f"[TTS] ERROR: Reference voice not found: {self.reference_voice}")
                print(f"[TTS] Record a 10-15 second clip and save it there.")
                self.reference_voice = None

    def initialize(self):
        """Load TTS engine. ElevenLabs needs no loading; Chatterbox loads model."""
        if self.engine == "elevenlabs":
            print("[TTS] ElevenLabs API ready (cloud TTS)")
        else:
            import torchaudio  # noqa: F401 - needed by chatterbox
            from chatterbox.tts import ChatterboxTTS

            device = self.chatterbox_config.get("device", "cuda")
            print(f"[TTS] Loading Chatterbox model (device={device})...")
            self.model = ChatterboxTTS.from_pretrained(device=device)
            print("[TTS] Chatterbox loaded and ready!")

    def synthesize(self, text, output_path=None):
        """Convert text to speech using the active engine."""
        if self.engine == "elevenlabs":
            return self._synthesize_elevenlabs(text, output_path)
        else:
            return self._synthesize_chatterbox(text, output_path)

    def _synthesize_elevenlabs(self, text, output_path=None):
        """Synthesize speech via ElevenLabs REST API with retry logic."""
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".mp3")

        start = time.time()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        body = {
            "text": text,
            "model_id": self.elevenlabs_model,
        }
        if self.elevenlabs_voice_settings:
            body["voice_settings"] = self.elevenlabs_voice_settings

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    url, headers=headers, json=body,
                    params={"output_format": self.elevenlabs_format},
                    timeout=15,
                )
                if resp.status_code != 200:
                    print(f"[TTS] ElevenLabs {resp.status_code}: {resp.text[:500]}")
                    if attempt < max_retries:
                        print(f"[TTS] Retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    return None
            except requests.RequestException as e:
                print(f"[TTS] ElevenLabs connection error: {e}")
                if attempt < max_retries:
                    print(f"[TTS] Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return None

            # Validate response is actually audio, not an error page
            content_type = resp.headers.get("content-type", "")
            if "audio" not in content_type and "octet-stream" not in content_type:
                print(f"[TTS] ElevenLabs returned non-audio ({content_type}): {resp.text[:300]}")
                if attempt < max_retries:
                    print(f"[TTS] Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return None

            # Valid audio response — save and return
            with open(output_path, "wb") as f:
                f.write(resp.content)

            elapsed = time.time() - start
            if attempt > 0:
                print(f"[TTS] ElevenLabs synthesized in {elapsed:.2f}s (succeeded on retry {attempt})")
            else:
                print(f"[TTS] ElevenLabs synthesized in {elapsed:.2f}s")
            return output_path

        return None

    def _synthesize_chatterbox(self, text, output_path=None):
        """Synthesize speech via local Chatterbox model."""
        import torchaudio as ta

        if self.model is None:
            self.initialize()

        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")

        start = time.time()

        generate_kwargs = {"text": text}
        if self.reference_voice:
            generate_kwargs["audio_prompt_path"] = self.reference_voice
        else:
            print("[TTS] WARNING: No reference voice — using default Chatterbox voice")

        wav = self.model.generate(**generate_kwargs)
        ta.save(output_path, wav, self.model.sr)

        elapsed = time.time() - start
        print(f"[TTS] Chatterbox synthesized in {elapsed:.2f}s")
        return output_path

    def generate_sound_effect(self, prompt, duration_seconds=None):
        """Generate a sound effect via ElevenLabs Sound Generation API with retry logic.

        Args:
            prompt: Text description of the sound (e.g. "dramatic thunder crash")
            duration_seconds: Duration 0.5-30s. None = auto-detect from prompt.

        Returns:
            Path to generated MP3 file, or None on error.
        """
        if not self.elevenlabs_api_key:
            print("[SFX] No ElevenLabs API key — cannot generate sound effects")
            return None

        output_path = tempfile.mktemp(suffix=".mp3")
        start = time.time()

        url = "https://api.elevenlabs.io/v1/sound-generation"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        body = {
            "text": prompt,
            "prompt_influence": self.sfx_prompt_influence,
        }
        if duration_seconds is not None:
            body["duration_seconds"] = max(0.5, min(30.0, duration_seconds))

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, json=body, headers=headers, timeout=30)
                if resp.status_code != 200:
                    print(f"[SFX] ElevenLabs {resp.status_code}: {resp.text[:500]}")
                    if attempt < max_retries:
                        print(f"[SFX] Retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    return None
            except requests.RequestException as e:
                print(f"[SFX] ElevenLabs connection error: {e}")
                if attempt < max_retries:
                    print(f"[SFX] Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return None

            content_type = resp.headers.get("content-type", "")
            if "audio" not in content_type and "octet-stream" not in content_type:
                print(f"[SFX] ElevenLabs returned non-audio ({content_type}): {resp.text[:300]}")
                if attempt < max_retries:
                    print(f"[SFX] Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return None

            # Valid audio response — save and return
            with open(output_path, "wb") as f:
                f.write(resp.content)

            elapsed = time.time() - start
            dur_str = f"{duration_seconds}s" if duration_seconds else "auto"
            if attempt > 0:
                print(f"[SFX] Generated in {elapsed:.2f}s: \"{prompt}\" ({dur_str}) (succeeded on retry {attempt})")
            else:
                print(f"[SFX] Generated in {elapsed:.2f}s: \"{prompt}\" ({dur_str})")
            return output_path

        return None

    def generate_sfx_audiogen(self, prompt, duration_seconds=None):
        """Generate a sound effect via local AudioGen Gradio server.

        AudioGen runs as a Docker container on port 7861.
        Falls back to ElevenLabs if the server is unreachable.

        Args:
            prompt: Text description of the sound (e.g. "dramatic thunder crash").
            duration_seconds: Duration 0.5-30s. None = 5s default.

        Returns:
            Path to generated WAV file, or None on error.
        """
        api_url = self.audiogen_config.get("api_url", "http://localhost:7861")
        dur = float(duration_seconds) if duration_seconds is not None else 5.0
        dur = max(0.5, min(30.0, dur))

        output_path = tempfile.mktemp(suffix=".wav")
        start = time.time()
        print(f"[AUDIOGEN] Generating: \"{prompt}\" ({dur}s)")

        predict_url = f"{api_url}/api/generate"
        payload = {"data": [prompt, dur]}

        try:
            resp = requests.post(predict_url, json=payload, timeout=60)
            if resp.status_code != 200:
                error_text = resp.text[:500] if resp.text else "(empty)"
                print(f"[AUDIOGEN] Server error {resp.status_code}: {error_text}")

                # Try alternate Gradio endpoint
                alt_url = f"{api_url}/run/generate"
                resp = requests.post(alt_url, json=payload, timeout=60)
                if resp.status_code != 200:
                    print(f"[AUDIOGEN] Alternate endpoint also failed: {resp.status_code}")
                    return None
        except requests.ConnectionError:
            print(f"[AUDIOGEN] Cannot connect to AudioGen at {api_url}")
            print(f"[AUDIOGEN] Start it: docker start audiogen")
            return None
        except requests.RequestException as e:
            print(f"[AUDIOGEN] Request error: {e}")
            return None

        # Parse Gradio response
        try:
            result = resp.json()
        except ValueError:
            # Response might be raw audio
            if len(resp.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                elapsed = time.time() - start
                print(f"[AUDIOGEN] Generated in {elapsed:.2f}s (raw audio)")
                return output_path
            print("[AUDIOGEN] Unexpected response format")
            return None

        # Extract audio from Gradio JSON response
        data = result.get("data", [])
        if not data:
            print("[AUDIOGEN] Empty response from server")
            return None

        audio_data = data[0]
        if isinstance(audio_data, dict):
            audio_url = audio_data.get("url") or audio_data.get("name") or audio_data.get("path")
            if audio_url:
                if audio_url.startswith("http"):
                    audio_resp = requests.get(audio_url, timeout=30)
                else:
                    audio_resp = requests.get(f"{api_url}/file={audio_url}", timeout=30)
                if audio_resp.status_code == 200 and len(audio_resp.content) > 1000:
                    with open(output_path, "wb") as f:
                        f.write(audio_resp.content)
                    elapsed = time.time() - start
                    print(f"[AUDIOGEN] Generated in {elapsed:.2f}s")
                    return output_path
        elif isinstance(audio_data, str):
            file_url = f"{api_url}/file={audio_data}"
            audio_resp = requests.get(file_url, timeout=30)
            if audio_resp.status_code == 200 and len(audio_resp.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(audio_resp.content)
                elapsed = time.time() - start
                print(f"[AUDIOGEN] Generated in {elapsed:.2f}s")
                return output_path

        print("[AUDIOGEN] Could not extract audio from response")
        return None

    def generate_music(self, prompt, duration_ms=10000, instrumental=False):
        """Generate music via ElevenLabs Music API with retry logic.

        Args:
            prompt: Text description of the music (e.g. "fantasy metal couplet")
            duration_ms: Length in milliseconds (3000-300000). Default 10s.
            instrumental: If True, forces instrumental. False lets prompt decide.

        Returns:
            Path to generated MP3 file, or None on error.
        """
        if not self.elevenlabs_api_key:
            print("[MUSIC] No ElevenLabs API key — cannot generate music")
            return None

        output_path = tempfile.mktemp(suffix=".mp3")
        start = time.time()

        url = "https://api.elevenlabs.io/v1/music/stream"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        body = {
            "prompt": prompt,
            "music_length_ms": max(3000, min(300000, duration_ms)),
            "force_instrumental": instrumental,
        }

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                print(f"[MUSIC] Generating: \"{prompt}\" ({duration_ms // 1000}s)...")
                resp = requests.post(
                    url, json=body, headers=headers,
                    stream=True, timeout=120,
                )
                if resp.status_code != 200:
                    # Read the error body (stream mode doesn't auto-read)
                    error_body = resp.text[:500] if resp.text else "(empty)"
                    print(f"[MUSIC] ElevenLabs {resp.status_code}: {error_body}")
                    if attempt < max_retries:
                        print(f"[MUSIC] Retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    return None
            except requests.RequestException as e:
                print(f"[MUSIC] ElevenLabs connection error: {e}")
                if attempt < max_retries:
                    print(f"[MUSIC] Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return None

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)

            # Validate the downloaded file isn't an error response
            file_size = os.path.getsize(output_path)
            if file_size < 1000:
                with open(output_path, "rb") as f:
                    head = f.read(200)
                if head[:1] in (b"{", b"<", b"[") or b"error" in head.lower():
                    print(f"[MUSIC] Downloaded file looks like an error ({file_size} bytes)")
                    if attempt < max_retries:
                        print(f"[MUSIC] Retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    return None

            elapsed = time.time() - start
            if attempt > 0:
                print(f"[MUSIC] Generated in {elapsed:.2f}s: \"{prompt}\" (succeeded on retry {attempt})")
            else:
                print(f"[MUSIC] Generated in {elapsed:.2f}s: \"{prompt}\"")
            return output_path

        return None

    def generate_music_acestep(self, lyrics, caption, duration_s=20):
        """Generate music via ACE-Step local Gradio API.

        ACE-Step runs as a local server (uv run acestep or acestep-api).
        Calls the Gradio predict endpoint with lyrics + caption (style).
        Supports voice cloning via reference audio.

        Args:
            lyrics: Song lyrics (newline-separated lines).
            caption: Style description (genre, instruments, mood).
            duration_s: Duration in seconds.

        Returns:
            Path to generated audio file, or None on error.
        """
        api_url = self.acestep_config.get("api_url", "http://localhost:7860")
        inference_steps = self.acestep_config.get("inference_steps", 8)
        guidance_scale = self.acestep_config.get("guidance_scale", 4.0)
        batch_size = self.acestep_config.get("batch_size", 1)
        audio_format = self.acestep_config.get("audio_format", "wav")
        # Voice reference for style transfer (reuse TTS reference or dedicated file)
        voice_ref = self.acestep_config.get("voice_reference") or self.reference_voice
        if voice_ref and not os.path.isabs(voice_ref):
            voice_ref = str(PROJECT_DIR / voice_ref)

        start = time.time()
        print(f"[ACESTEP] Generating song ({duration_s}s): {caption[:60]}...")
        print(f"[ACESTEP] Lyrics: {lyrics.replace(chr(10), ' / ')}")

        # Build Gradio API request — ACE-Step's /generate endpoint
        # The Gradio API expects positional args matching the UI inputs
        predict_url = f"{api_url}/api/generate"
        payload = {
            "data": [
                caption,           # tags / style description
                lyrics,            # lyrics text
                False,             # instrumental (False = include vocals)
                duration_s,        # duration in seconds
                inference_steps,   # inference steps
                guidance_scale,    # CFG scale
                -1,                # seed (-1 = random)
                batch_size,        # batch size
                audio_format,      # output format
            ]
        }

        # If voice reference is set, try the cover/style-transfer endpoint
        if voice_ref and os.path.exists(voice_ref):
            print(f"[ACESTEP] Voice reference: {voice_ref}")

        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(predict_url, json=payload, timeout=120)
                if resp.status_code != 200:
                    error_text = resp.text[:500] if resp.text else "(empty)"
                    print(f"[ACESTEP] Server error {resp.status_code}: {error_text}")

                    # Try the Gradio /run/ style endpoint as fallback
                    if attempt == 0:
                        alt_url = f"{api_url}/run/generate"
                        print(f"[ACESTEP] Trying alternate endpoint: {alt_url}")
                        resp = requests.post(alt_url, json=payload, timeout=120)
                        if resp.status_code == 200:
                            pass  # fall through to response handling
                        else:
                            print(f"[ACESTEP] Alternate also failed: {resp.status_code}")
                            if attempt < max_retries:
                                time.sleep(1)
                                continue
                            return None
                    else:
                        return None
            except requests.ConnectionError:
                print(f"[ACESTEP] Cannot connect to ACE-Step at {api_url}")
                print(f"[ACESTEP] Start it: docker start acestep")
                return None
            except requests.RequestException as e:
                print(f"[ACESTEP] Request error: {e}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return None

            # Parse Gradio response — contains file paths or base64 audio
            try:
                result = resp.json()
            except ValueError:
                # Response might be raw audio
                if len(resp.content) > 1000:
                    output_path = tempfile.mktemp(suffix=f".{audio_format}")
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    elapsed = time.time() - start
                    print(f"[ACESTEP] Generated in {elapsed:.2f}s (raw audio)")
                    return output_path
                print(f"[ACESTEP] Unexpected response format")
                return None

            # Gradio JSON response: {"data": [...]}
            # Audio files are usually returned as file paths or dicts with "name" key
            data = result.get("data", [])
            if not data:
                print(f"[ACESTEP] Empty response from server")
                return None

            # Find the first audio output (could be a path, dict, or nested)
            audio_data = data[0] if data else None
            if isinstance(audio_data, dict):
                # Gradio file format: {"name": "/tmp/xxx.wav", "data": null, ...}
                audio_url = audio_data.get("url") or audio_data.get("name") or audio_data.get("path")
                if audio_url:
                    # If it's a URL, download it; if it's a local path on the server, fetch via file endpoint
                    if audio_url.startswith("http"):
                        audio_resp = requests.get(audio_url, timeout=30)
                    else:
                        # Gradio serves files via /file= endpoint
                        file_url = f"{api_url}/file={audio_url}"
                        audio_resp = requests.get(file_url, timeout=30)
                    if audio_resp.status_code == 200 and len(audio_resp.content) > 1000:
                        output_path = tempfile.mktemp(suffix=f".{audio_format}")
                        with open(output_path, "wb") as f:
                            f.write(audio_resp.content)
                        elapsed = time.time() - start
                        print(f"[ACESTEP] Generated in {elapsed:.2f}s")
                        return output_path
            elif isinstance(audio_data, str):
                # Direct file path on the server
                file_url = f"{api_url}/file={audio_data}"
                audio_resp = requests.get(file_url, timeout=30)
                if audio_resp.status_code == 200 and len(audio_resp.content) > 1000:
                    output_path = tempfile.mktemp(suffix=f".{audio_format}")
                    with open(output_path, "wb") as f:
                        f.write(audio_resp.content)
                    elapsed = time.time() - start
                    print(f"[ACESTEP] Generated in {elapsed:.2f}s")
                    return output_path
            elif isinstance(audio_data, list):
                # Batch results — take the first one
                first = audio_data[0] if audio_data else None
                if isinstance(first, dict):
                    audio_url = first.get("url") or first.get("name") or first.get("path")
                    if audio_url:
                        if audio_url.startswith("http"):
                            audio_resp = requests.get(audio_url, timeout=30)
                        else:
                            audio_resp = requests.get(f"{api_url}/file={audio_url}", timeout=30)
                        if audio_resp.status_code == 200 and len(audio_resp.content) > 1000:
                            output_path = tempfile.mktemp(suffix=f".{audio_format}")
                            with open(output_path, "wb") as f:
                                f.write(audio_resp.content)
                            elapsed = time.time() - start
                            print(f"[ACESTEP] Generated in {elapsed:.2f}s")
                            return output_path

            print(f"[ACESTEP] Could not extract audio from response")
            if attempt < max_retries:
                time.sleep(1)
                continue
            return None

        return None

    def _play_or_retry(self, audio_path, text):
        """Play audio file, retrying synthesis once if corrupt audio is detected.

        ElevenLabs has a rare 'corrupt speech' bug that produces noise.
        When play_audio() detects this, we re-call the API for that chunk
        rather than leaving a gap in the response.
        """
        if not audio_path:
            return
        success = play_audio(audio_path)
        try:
            os.unlink(audio_path)
        except OSError:
            pass
        if not success:
            print("[TTS] Corrupt audio detected — regenerating chunk...")
            retry_path = self.synthesize(text)
            if retry_path:
                play_audio(retry_path)  # Don't retry a second time
                try:
                    os.unlink(retry_path)
                except OSError:
                    pass

    def speak(self, text):
        """Synthesize and play audio with paired-sentence streaming.

        Groups sentences into pairs (every 2 sentences = 1 TTS call).
        1-2 sentences: single call, no split.
        3+: pairs, with the next pair synthesizing in the background
        while the current pair plays.

        If a chunk comes back as corrupt audio, re-calls the API once.
        """
        sentences = split_sentences(text)
        if not sentences:
            return

        chunks = _group_into_pairs(sentences)

        if len(chunks) == 1:
            audio_path = self.synthesize(chunks[0])
            self._play_or_retry(audio_path, chunks[0])
            return

        # Multiple chunks: synthesize next while playing current
        next_audio = [None]

        def synth_bg(chunk_text):
            next_audio[0] = self.synthesize(chunk_text)

        current_audio = self.synthesize(chunks[0])
        current_text = chunks[0]

        for i in range(1, len(chunks)):
            bg_thread = threading.Thread(target=synth_bg, args=(chunks[i],))
            bg_thread.start()

            self._play_or_retry(current_audio, current_text)

            bg_thread.join()
            current_audio = next_audio[0]
            current_text = chunks[i]
            next_audio[0] = None

        self._play_or_retry(current_audio, current_text)

    def play_response(self, text):
        """Play a response that may contain speech, sound effects, and music.

        Parses {{sfx: description}} and {{music: description | 30s}} tags.
        PARALLEL PRELOADING: all media segments start generating immediately
        in background threads while earlier text segments are being spoken.
        By the time we reach the media tag, it may already be ready.

        Music auto-prepends an intro SFX (e.g. guitar plug-in) if configured
        via music_intro_sfx in active-character.json.
        """
        # Only parse media tags when at least one media engine is available
        has_media_engine = (
            self.engine == "elevenlabs"
            or self.music_engine == "acestep"
            or self.sfx_engine == "audiogen"
        )
        if not has_media_engine:
            self.speak(text)
            return

        segments = parse_media_tags(text)

        # No media tags found — just speak normally
        if all(s[0] == "text" for s in segments):
            self.speak(text)
            return

        # --- Parallel preloading: kick off ALL media generations NOW ---
        preloads = {}

        def _bg_sfx(result, prompt, duration):
            if self.sfx_engine == "audiogen":
                audio = self.generate_sfx_audiogen(prompt, duration)
                if audio is None and self.elevenlabs_api_key:
                    print("[AUDIOGEN] Falling back to ElevenLabs SFX...")
                    audio = self.generate_sound_effect(prompt, duration)
                result[0] = audio
            else:
                result[0] = self.generate_sound_effect(prompt, duration)

        def _bg_music(result, prompt, dur_ms):
            result[0] = self.generate_music(prompt, dur_ms)

        def _bg_music_acestep(result, lyrics, caption, dur_s):
            audio_path = self.generate_music_acestep(lyrics, caption, dur_s)
            if audio_path is None and self.elevenlabs_api_key:
                # Fallback to ElevenLabs if ACE-Step is down
                print("[ACESTEP] Falling back to ElevenLabs...")
                full_prompt = f"{caption}\n\n{lyrics}" if caption else lyrics
                audio_path = self.generate_music(full_prompt, int(dur_s * 1000))
            result[0] = audio_path

        def _bg_intro(result, prompt):
            if self.sfx_engine == "audiogen":
                audio = self.generate_sfx_audiogen(prompt, 5)
                if audio is None and self.elevenlabs_api_key:
                    audio = self.generate_sound_effect(prompt, 5)
                result[0] = audio
            else:
                result[0] = self.generate_sound_effect(prompt, 5)

        for i, seg in enumerate(segments):
            if seg[0] == "sfx":
                result = [None]
                dur = seg[2] if seg[2] is not None else self.sfx_default_duration
                t = threading.Thread(target=_bg_sfx, args=(result, seg[1], dur))
                t.start()
                preloads[i] = (t, result)

            elif seg[0] == "music":
                dur_s = seg[2] if seg[2] is not None else self.music_default_duration
                dur_ms = int(dur_s * 1000)
                # Preload the music itself
                music_result = [None]
                t_music = threading.Thread(
                    target=_bg_music, args=(music_result, seg[1], dur_ms)
                )
                t_music.start()
                # Also preload the intro SFX if configured
                intro_result = [None]
                t_intro = None
                if self.music_intro_sfx:
                    t_intro = threading.Thread(
                        target=_bg_intro, args=(intro_result, self.music_intro_sfx)
                    )
                    t_intro.start()
                preloads[i] = (t_music, music_result, t_intro, intro_result)

            elif seg[0] == "song":
                # {{song: lyrics}} — combine lyrics with music_style from config
                lyrics = seg[1]
                # Convert / separators to newlines for the music prompt
                lyrics_formatted = "\n".join(
                    line.strip() for line in lyrics.split("/") if line.strip()
                )
                caption = self.music_style or ""
                # Duration scales with character count: 160ms per character (min 8s)
                lyric_chars = sum(len(l.strip()) for l in lyrics.split("/") if l.strip())
                dur_s = max(8, int(lyric_chars * 0.16))

                music_result = [None]
                if self.music_engine == "acestep":
                    # ACE-Step: send lyrics + style separately (it handles combining)
                    t_music = threading.Thread(
                        target=_bg_music_acestep,
                        args=(music_result, lyrics_formatted, caption, dur_s),
                    )
                else:
                    # ElevenLabs: combine style + lyrics into one prompt
                    full_prompt = f"{caption}\n\n{lyrics_formatted}" if caption else lyrics_formatted
                    dur_ms = int(dur_s * 1000)
                    t_music = threading.Thread(
                        target=_bg_music, args=(music_result, full_prompt, dur_ms),
                    )
                t_music.start()
                intro_result = [None]
                t_intro = None
                if self.music_intro_sfx:
                    t_intro = threading.Thread(
                        target=_bg_intro, args=(intro_result, self.music_intro_sfx)
                    )
                    t_intro.start()
                preloads[i] = (t_music, music_result, t_intro, intro_result)
                print(f"[SONG] Engine: {self.music_engine}")
                print(f"[SONG] Lyrics: {lyrics_formatted.replace(chr(10), ' / ')}")

        print(f"[MEDIA] Preloading {len(preloads)} media segment(s) in background...")

        # --- Play segments in order ---
        for i, seg in enumerate(segments):
            seg_type = seg[0]

            if seg_type == "text":
                self.speak(seg[1])

            elif seg_type == "sfx" and i in preloads:
                t, result = preloads[i]
                if t.is_alive():
                    print("[SFX] Waiting for sound effect...")
                t.join()
                audio = result[0]
                if audio:
                    play_audio(audio)
                    try:
                        os.unlink(audio)
                    except OSError:
                        pass

            elif seg_type in ("music", "song") and i in preloads:
                t_music, music_result, t_intro, intro_result = preloads[i]
                # Play intro SFX first (guitar plug-in etc.)
                if t_intro is not None:
                    if t_intro.is_alive():
                        print("[SFX] Waiting for intro sound...")
                    t_intro.join()
                    intro_audio = intro_result[0]
                    if intro_audio:
                        play_audio(intro_audio)
                        try:
                            os.unlink(intro_audio)
                        except OSError:
                            pass
                # Then play the music/song
                label = "SONG" if seg_type == "song" else "MUSIC"
                if t_music.is_alive():
                    print(f"[{label}] Waiting for generation to finish...")
                t_music.join()
                audio = music_result[0]
                if audio:
                    play_audio(audio)
                    try:
                        os.unlink(audio)
                    except OSError:
                        pass


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def split_sentences(text):
    """Split text into sentences for streaming TTS.

    Splits on sentence-ending punctuation (.!?) followed by a space or end.
    Keeps the punctuation with the sentence.
    Filters out tag-only fragments (e.g. just "[laughs]") that have no speakable text.
    """
    # Split on .!? followed by space or end-of-string, keeping the delimiter
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter out empty strings and tag-only fragments
    result = []
    for s in parts:
        s = s.strip()
        if not s:
            continue
        # Check if there's any actual text after removing [tags]
        without_tags = re.sub(r'\[.*?\]', '', s).strip()
        if without_tags:
            result.append(s)
        elif result:
            # Merge orphan tags into the previous sentence
            result[-1] = result[-1] + " " + s
        # else: orphan tag at the start — drop it
    return result


def _group_into_pairs(sentences):
    """Group sentences into pairs for smoother TTS streaming.

    1 sentence  → ['Hello.']                          (no split)
    2 sentences → ['Hello. Goodbye.']                  (no split)
    3 sentences → ['A. B.', 'C.']                      (pair + remainder)
    4 sentences → ['A. B.', 'C. D.']                   (two pairs)
    5 sentences → ['A. B.', 'C. D.', 'E.']             (two pairs + remainder)
    """
    if len(sentences) <= 2:
        return [" ".join(sentences)]

    chunks = []
    for i in range(0, len(sentences), 2):
        chunk = " ".join(sentences[i:i + 2])
        chunks.append(chunk)
    return chunks


def parse_media_tags(text):
    """Parse {{sfx: ...}}, {{music: ...}}, and {{song: ...}} tags from a response.

    Tags embedded by Gemini in the response text:
        {{sfx: dramatic thunder crash}}          — sound effect, auto duration
        {{sfx: explosion | 3}}                   — sound effect, 3 seconds
        {{music: epic viking battle drums | 30}} — music, 30 seconds
        {{song: lyrics line 1 / lyrics line 2}}  — song (lyrics only, style from config)

    The {{song}} tag is the preferred format for character singing. Gemini
    writes ONLY lyrics (separated by /). The pipeline combines them with
    music_style from active-character.json to build the full ElevenLabs prompt.
    This prevents lyrics from being spoken by TTS AND sung — they only get sung.

    Returns a list of segments:
        [('text', 'Hello!'), ('sfx', 'explosion', 3.0), ('song', 'lyrics...', None)]
    Each segment is a tuple: (type, content, duration_or_None)
    """
    pattern = r'\{\{(sfx|music|song):\s*([^}]+)\}\}'
    segments = []
    last_end = 0

    for match in re.finditer(pattern, text):
        # Capture any text before this tag
        before = text[last_end:match.start()].strip()
        if before:
            segments.append(("text", before, None))

        media_type = match.group(1)   # 'sfx', 'music', or 'song'
        content = match.group(2).strip()

        # Parse optional duration: "description | 5" (not used for song)
        duration = None
        if media_type != "song" and "|" in content:
            desc, dur_str = content.rsplit("|", 1)
            desc = desc.strip()
            dur_str = dur_str.strip().rstrip("s")
            try:
                duration = float(dur_str)
            except ValueError:
                desc = content  # keep full string if parse fails
        else:
            desc = content

        segments.append((media_type, desc, duration))
        last_end = match.end()

    # Remaining text after the last tag
    remaining = text[last_end:].strip()
    if remaining:
        segments.append(("text", remaining, None))

    return segments


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------
def play_audio(audio_path):
    """Play an audio file (WAV or MP3) through the default speaker.

    Validates the file before playing to prevent ear-destroying noise.
    ElevenLabs has a known rare bug ("corrupt speech") where the model
    generates distorted/noisy audio unpredictably. We detect this
    client-side and skip it rather than blasting noise through speakers.

    Safety checks:
    1. File size — tiny files are likely error responses, not audio
    2. NaN/Inf values — replace with silence
    3. Peak amplitude — normalize if clipping (> 1.0)
    4. RMS energy — skip if extremely high (likely noise, not speech)
    5. Soft limiter — clamp all samples to safe range

    Returns:
        True if audio played successfully, False if skipped due to corruption.
    """
    try:
        file_size = os.path.getsize(audio_path)
        if file_size < 1000:
            # Suspiciously small — probably an error response, not audio
            with open(audio_path, "rb") as f:
                head = f.read(200)
            # Check if it looks like text (JSON/HTML error) rather than audio
            if head[:1] in (b"{", b"<", b"[") or b"error" in head.lower():
                print(f"[AUDIO] Skipping bad file ({file_size} bytes) — looks like an error response")
                return False

        data, sample_rate = sf.read(audio_path)

        # --- Waveform safety checks ---

        if data.size == 0:
            print("[AUDIO] Skipping empty audio data")
            return False

        # Check for NaN/Inf (can happen with corrupt decode)
        if not np.all(np.isfinite(data)):
            nan_count = np.count_nonzero(~np.isfinite(data))
            print(f"[AUDIO] WARNING: {nan_count} NaN/Inf samples found — replacing with silence")
            data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

        # Check peak amplitude — ElevenLabs speech rarely exceeds 1.0.
        # Music can legitimately clip to ~1.05. Real corrupt audio hits 1.3+.
        peak = np.max(np.abs(data))
        if peak > 1.2:
            print(f"[AUDIO] Skipping corrupt audio (peak={peak:.2f}) — triggering retry")
            return False
        if peak > 1.0:
            # Mild clipping — normalize rather than reject
            data = data / peak * 0.95

        # Check RMS energy — normal speech is typically 0.05-0.3 RMS
        # Anything above 0.7 is almost certainly noise/corruption
        rms = np.sqrt(np.mean(data ** 2))
        if rms > 0.7:
            print(f"[AUDIO] Skipping corrupt audio (RMS={rms:.2f}) — triggering retry")
            return False

        # Soft limiter — clamp to safe range to prevent ear damage
        data = np.clip(data, -0.95, 0.95)

        # Pad 250ms of silence at the end to prevent audio cutoff.
        # PortAudio bug on Windows: sd.wait() returns early, clipping the
        # tail of the audio. 150ms wasn't enough, 250ms still clips — 400ms.
        # See: https://github.com/spatialaudio/python-sounddevice/issues/283
        pad_samples = int(sample_rate * 0.40)
        if data.ndim == 1:
            padding = np.zeros(pad_samples, dtype=data.dtype)
        else:
            padding = np.zeros((pad_samples, data.shape[1]), dtype=data.dtype)
        data = np.concatenate([data, padding])

        sd.play(data, sample_rate)
        sd.wait()
        return True
    except Exception as e:
        print(f"[AUDIO] Could not play {audio_path}: {e}")
        sd.stop()  # Kill any noise that started
        return False


def _resolve_input_device(device_spec):
    """Resolve a device specifier to a PortAudio device index.

    Args:
        device_spec: None (system default), int (device index), or str
                     (substring match against device name, case-insensitive).
    Returns:
        int device index, or None for system default.
    """
    if device_spec is None:
        return None
    if isinstance(device_spec, int) or (isinstance(device_spec, str) and device_spec.isdigit()):
        return int(device_spec)
    # Substring match against device names
    needle = str(device_spec).lower()
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0 and needle in dev["name"].lower():
            print(f"[AUDIO] Matched input device {i}: {dev['name']}")
            return i
    print(f"[AUDIO] WARNING: No input device matching '{device_spec}' — using system default")
    return None


def _find_same_mic_on_other_backends(device_idx):
    """Find the same physical mic on other audio backends.

    Windows exposes each mic multiple times (MME, DirectSound, WASAPI,
    WDM-KS).  Given one index, return alternatives sorted by reliability:
    WASAPI > DirectSound > others.

    Returns list of (device_index, hostapi_name) tuples, best first.
    """
    all_devices = sd.query_devices()
    hostapi_names = [h["name"] for h in sd.query_hostapis()]

    # Get the base mic name (strip backend-specific suffixes)
    if device_idx is not None:
        target_name = all_devices[device_idx]["name"].lower()
    else:
        # System default — get its name
        default_info = sd.query_devices(kind="input")
        target_name = default_info["name"].lower()

    # Find all input devices with the same name on different backends
    BACKEND_PRIORITY = {
        "Windows WASAPI": 0,
        "Windows DirectSound": 1,
        "MME": 2,
        "Windows WDM-KS": 3,
    }

    alternatives = []
    for i, dev in enumerate(all_devices):
        if i == device_idx:
            continue  # skip the one that already failed
        if dev["max_input_channels"] <= 0:
            continue
        if dev["name"].lower() == target_name:
            api = hostapi_names[dev["hostapi"]]
            priority = BACKEND_PRIORITY.get(api, 99)
            alternatives.append((priority, i, api))

    alternatives.sort()
    return [(idx, api) for _, idx, api in alternatives]


def _try_open_stream(device, sample_rate, channels, hostapi_name=None, **kwargs):
    """Try to open an InputStream on a specific device, trying multiple rates.

    For WASAPI devices, automatically applies WasapiSettings(auto_convert=True).

    Returns (stream, actual_rate) or (None, None) if all rates fail.
    """
    rates_to_try = [sample_rate]
    for r in [48000, 44100, 16000, 22050, 8000]:
        if r not in rates_to_try:
            rates_to_try.append(r)

    dev_kwargs = {}
    if device is not None:
        dev_kwargs["device"] = device

    # WASAPI works best with auto_convert (handles rate/format negotiation)
    extra = None
    if hostapi_name == "Windows WASAPI":
        extra = sd.WasapiSettings(exclusive=False, auto_convert=True)

    last_error = None
    for rate in rates_to_try:
        try:
            stream = sd.InputStream(
                samplerate=rate, channels=channels,
                extra_settings=extra, **dev_kwargs, **kwargs,
            )
            return stream, rate
        except sd.PortAudioError as e:
            last_error = e

    # Log the final error for this backend so we can diagnose
    if last_error is not None:
        api_label = hostapi_name or "default"
        print(f"[AUDIO]   ^ {api_label} error: {last_error}")

    return None, None


def _open_mic_stream(sample_rate, channels, device=None, **kwargs):
    """Open a mic InputStream with robust fallbacks for rate AND backend.

    Strategy:
    1. Try the requested device at multiple sample rates.
    2. If that fails, find the same physical mic on other Windows audio
       backends (WASAPI first, then DirectSound, etc.) and try those.
    3. Whisper resamples internally so any recording rate is fine.

    Args:
        sample_rate: Preferred recording rate (e.g. 16000).
        channels: Number of channels (usually 1).
        device: PortAudio device index (int) or None for default.
        **kwargs: Extra args passed to sd.InputStream (dtype, callback, etc.)

    Returns:
        (stream, actual_sample_rate) — caller must stream.start() / .close().

    Raises:
        RuntimeError if nothing works at all.
    """
    # --- Attempt 1: Try the requested device directly ---
    stream, rate = _try_open_stream(device, sample_rate, channels, **kwargs)
    if stream is not None:
        if rate != sample_rate:
            print(f"[AUDIO] Mic opened at {rate} Hz (requested {sample_rate})")
        return stream, rate

    # --- Attempt 2: Same mic, different backend ---
    alternatives = _find_same_mic_on_other_backends(device)
    for alt_idx, alt_api in alternatives:
        alt_name = sd.query_devices(alt_idx)["name"]
        print(f"[AUDIO] Trying {alt_name} via {alt_api} (device {alt_idx})...")
        stream, rate = _try_open_stream(
            alt_idx, sample_rate, channels, hostapi_name=alt_api, **kwargs,
        )
        if stream is not None:
            print(f"[AUDIO] Opened via {alt_api} at {rate} Hz")
            return stream, rate

    # --- Nothing worked ---
    dev_name = "system default"
    if device is not None:
        try:
            dev_name = sd.query_devices(device)["name"]
        except Exception:
            dev_name = f"device {device}"
    raise RuntimeError(
        f"Could not open mic '{dev_name}' on any backend or sample rate.\n"
        f"  Run with --list-audio to see available devices.\n"
        f"  Check: Windows Settings > Privacy > Microphone > Allow apps"
    )


def record_audio_ptt(config):
    """Record audio with push-to-talk. Returns path to WAV file."""
    import keyboard

    audio_config = config["audio"]
    ptt_key = audio_config["ptt_key"]
    sample_rate = audio_config["sample_rate"]
    channels = audio_config["channels"]
    device = _resolve_input_device(audio_config.get("input_device"))

    frames = []
    recording = False

    print(f"\n  Press and hold [{ptt_key.upper()}] to talk to Hoggle...")
    print("  (Press Ctrl+C to quit)\n")

    # Wait for key press
    keyboard.wait(ptt_key)

    # Start recording
    recording = True
    print("  [RECORDING] Speak now...")

    def audio_callback(indata, frame_count, time_info, status):
        if recording:
            frames.append(indata.copy())

    stream, actual_rate = _open_mic_stream(
        sample_rate, channels, device=device,
        dtype="float32", callback=audio_callback,
    )

    with stream:
        # Wait for key release
        keyboard.wait(ptt_key, suppress=False, trigger_on_release=True)
        recording = False

    print("  [DONE] Processing...")

    if not frames:
        return None

    # Save to temp WAV file
    audio_data = np.concatenate(frames, axis=0)
    wav_path = tempfile.mktemp(suffix=".wav")
    sf.write(wav_path, audio_data, actual_rate)
    return wav_path


# ---------------------------------------------------------------------------
# n8n integration
# ---------------------------------------------------------------------------
def send_to_hoggle(message, config, history=None):
    """Send a message to the n8n crystal loader webhook and get response.

    Args:
        message: The user's current message.
        config: Pipeline config dict.
        history: Optional list of prior turns as
                 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
                 Sent to Gemini for conversational context.
    """
    n8n_config = config["n8n"]
    url = n8n_config["webhook_url"]

    body = {"message": message}
    if history:
        body["history"] = history

    start = time.time()
    try:
        resp = requests.post(
            url,
            json=body,
            timeout=n8n_config.get("timeout", 30),
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[N8N] Connection error: {e}")
        return None

    # Parse JSON — show raw response if it fails
    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError):
        body_preview = resp.text[:300] if resp.text else "(empty response)"
        print(f"[N8N] Bad response from n8n (not JSON). Status {resp.status_code}:")
        print(f"[N8N] Body: {body_preview}")
        return None

    elapsed = time.time() - start
    response_text = data.get("response", "")
    classification = data.get("classification", "unknown")
    crystal_count = data.get("crystal_count", 0)
    mode = data.get("active_mode", "unknown")

    character = data.get("active_character", "unknown")
    print(f"[N8N] Response in {elapsed:.2f}s | char={character} | mode={mode} | class={classification} | crystals={crystal_count}")
    return response_text


# ---------------------------------------------------------------------------
# Main pipeline modes
# ---------------------------------------------------------------------------
def run_voice_loop(config):
    """Full voice pipeline: PTT → STT → Hoggle → TTS → Speaker."""
    stt = SpeechToText(config)
    tts = TextToSpeech(config)

    character = config.get("_active_character", "hoggle").upper()
    tts_engine = config.get("_tts_engine", "chatterbox")
    print("=" * 60)
    print(f"  {character} VOICE PIPELINE")
    print("=" * 60)
    print(f"  Character:  {character}")
    print(f"  STT Model:  {config['whisper']['model']}")
    print(f"  TTS Engine: {tts_engine}")
    music_engine = config.get("_music_engine", "elevenlabs")
    sfx_engine = config.get("_sfx_engine", "elevenlabs")
    print(f"  Music:      {music_engine}")
    print(f"  SFX:        {sfx_engine}")
    print(f"  PTT Key:    {config['audio']['ptt_key']}")
    print(f"  n8n URL:    {config['n8n']['webhook_url']}")
    print("=" * 60)

    print("\n[INIT] Loading models (this takes a moment)...\n")
    stt.initialize()
    tts.initialize()

    MAX_HISTORY_TURNS = 10
    history = []

    while True:
        try:
            total_start = time.time()

            # Step 1: Record audio (PTT)
            wav_path = record_audio_ptt(config)
            if not wav_path:
                print("[SKIP] No audio captured.")
                continue

            # Step 2: Transcribe (STT)
            text = stt.transcribe(wav_path)
            os.unlink(wav_path)  # Clean up recording

            if not text or not text.strip():
                print("[SKIP] No speech detected.")
                continue

            # Step 3: Send to Hoggle via n8n
            response = send_to_hoggle(text, config, history=history)
            if not response:
                print("[SKIP] No response from Hoggle.")
                continue

            print(f"\n  >>> {response}\n")

            # Track conversation history
            clean_response = re.sub(r'\{\{(sfx|music|song):[^}]+\}\}', '', response).strip()
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": clean_response})
            if len(history) > MAX_HISTORY_TURNS * 2:
                history = history[-(MAX_HISTORY_TURNS * 2):]

            # Step 4: Speak the response (TTS + SFX/music if tagged)
            tts.play_response(response)

            total = time.time() - total_start
            print(f"[PIPELINE] Total round-trip: {total:.2f}s")

        except KeyboardInterrupt:
            print("\n\nHoggle: See ya later! *oinks and fades into the Backrooms*")
            break


def _get_hybrid_input(stt, audio_config):
    """Get user input via typing OR Ctrl+Space voice recording.

    Uses msvcrt (Windows) for non-blocking character input so we can
    simultaneously poll for the Ctrl+Space PTT hotkey.

    Type normally and press Enter to send text.
    Hold Ctrl+Space to record from mic, release to transcribe.
    Type 'quit' and Enter to exit.

    Returns:
        str with the message, or None to signal quit.
    """
    import keyboard
    import msvcrt

    buffer = []
    sys.stdout.write("  You: ")
    sys.stdout.flush()

    while True:
        # --- Check for Ctrl+Space (voice PTT) ---
        if keyboard.is_pressed("ctrl") and keyboard.is_pressed("space"):
            # Clear the typed text from the line
            line = "  You: " + "".join(buffer)
            sys.stdout.write("\r" + " " * len(line) + "\r")
            sys.stdout.write("  [RECORDING] Speak now...")
            sys.stdout.flush()

            # Small debounce — let both keys settle
            time.sleep(0.2)

            # Record audio while keys are held
            frames = []
            configured_rate = audio_config.get("sample_rate", 16000)
            channels = audio_config.get("channels", 1)
            device = _resolve_input_device(audio_config.get("input_device"))

            stream, actual_rate = _open_mic_stream(
                configured_rate, channels, device=device, dtype="float32",
            )
            stream.start()

            while keyboard.is_pressed("ctrl") or keyboard.is_pressed("space"):
                data, _ = stream.read(int(actual_rate * 0.1))  # 100ms chunks
                frames.append(data.copy())

            stream.stop()
            stream.close()

            # Need at least 0.3s of audio (not an accidental tap)
            min_frames = int(0.3 / 0.1)  # 3 chunks of 100ms
            if len(frames) < min_frames:
                sys.stdout.write("\r  [Too short — hold longer]      \n")
                buffer = []
                sys.stdout.write("  You: ")
                sys.stdout.flush()
                continue

            sys.stdout.write("\r  [TRANSCRIBING]...               ")
            sys.stdout.flush()

            # Save to temp WAV and transcribe
            audio_data = np.concatenate(frames, axis=0)
            wav_path = tempfile.mktemp(suffix=".wav")
            sf.write(wav_path, audio_data, actual_rate)

            text = stt.transcribe(wav_path)
            try:
                os.unlink(wav_path)
            except OSError:
                pass

            if text and text.strip():
                sys.stdout.write(f"\r  You: {text.strip()}\n")
                sys.stdout.flush()
                return text.strip()
            else:
                sys.stdout.write("\r  [No speech detected]            \n")
                buffer = []
                sys.stdout.write("  You: ")
                sys.stdout.flush()
                continue

        # --- Check for keyboard input (non-blocking) ---
        if msvcrt.kbhit():
            ch = msvcrt.getwch()

            if ch == "\r":  # Enter
                sys.stdout.write("\n")
                sys.stdout.flush()
                text = "".join(buffer).strip()
                if not text:
                    # Empty enter — just re-show prompt
                    buffer = []
                    sys.stdout.write("  You: ")
                    sys.stdout.flush()
                    continue
                if text.lower() in ("quit", "exit", "q"):
                    return None
                return text

            elif ch == "\b":  # Backspace
                if buffer:
                    buffer.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()

            elif ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt

            elif ch in ("\x00", "\xe0"):
                # Special key prefix (arrow keys, function keys) — consume second byte
                msvcrt.getwch()

            elif ch == " ":
                # Normal space (not Ctrl+Space since we checked that above)
                buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()

            else:
                buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()

        time.sleep(0.01)  # 10ms poll — prevents busy-waiting


def run_type_mode(config):
    """Hybrid mode: type messages OR hold Ctrl+Space to talk. Hear spoken response."""
    tts = TextToSpeech(config)

    character = config.get("_active_character", "hoggle").upper()
    tts_engine = config.get("_tts_engine", "chatterbox")
    music_engine = config.get("_music_engine", "elevenlabs")
    sfx_engine = config.get("_sfx_engine", "elevenlabs")
    print("=" * 60)
    print(f"  {character} HYBRID MODE (type or talk, hear speech)")
    print(f"  Music: {music_engine} | SFX: {sfx_engine}")
    print("=" * 60)

    # Initialize TTS (always needed)
    print(f"  Loading TTS ({tts_engine})...")
    tts.initialize()

    # Initialize STT (needed for Ctrl+Space voice input)
    stt = None
    try:
        stt = SpeechToText(config)
        print(f"  Loading STT ({config['whisper']['model']})...")
        stt.initialize()
        voice_ready = True
    except Exception as e:
        print(f"  [STT] Could not load Whisper: {e}")
        print(f"  [STT] Voice input disabled — type mode only")
        voice_ready = False

    print()
    if voice_ready:
        print("  Type a message + Enter, or hold [CTRL+SPACE] to talk.")
    else:
        print("  Type a message and press Enter.")
    print("  Type 'quit' to exit.\n")

    # Conversation history buffer (last N turns for Gemini context)
    MAX_HISTORY_TURNS = 10  # 10 turns = 5 back-and-forth exchanges
    history = []

    while True:
        try:
            # Use hybrid input if STT is ready AND we're on Windows
            if voice_ready and sys.platform == "win32":
                message = _get_hybrid_input(stt, config["audio"])
            else:
                # Fallback: text-only input
                message = input("  You: ").strip()
                if not message:
                    continue
                if message.lower() in ("quit", "exit", "q"):
                    message = None

            if message is None:
                print("\n  >>> Later! *oinks*")
                break

            response = send_to_hoggle(message, config, history=history)
            if response:
                print(f"  >>> {response}\n")
                # Add this exchange to history (strip media tags for cleaner context)
                clean_response = re.sub(r'\{\{(sfx|music|song):[^}]+\}\}', '', response).strip()
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": clean_response})
                # Trim history to max turns
                if len(history) > MAX_HISTORY_TURNS * 2:
                    history = history[-(MAX_HISTORY_TURNS * 2):]
                tts.play_response(response)

        except KeyboardInterrupt:
            print("\n\n  >>> See ya! *fades*")
            break


def test_tts(config):
    """Test TTS engine independently."""
    tts = TextToSpeech(config)
    tts.initialize()

    character = config.get("_active_character", "hoggle")
    tts_engine = config.get("_tts_engine", "chatterbox")

    if character == "forte":
        test_lines = [
            "Hey! Ready to make some noise? I'm Forte!",
            "BOOM! That hit like a Perfect Fifth!",
            "Let me tune into that real quick.",
        ]
    else:
        test_lines = [
            "Hey hey! What's oinking? I'm Hoggle, Mr. B's teaching assistant!",
            "Welcome to Multimedia Heroes! Ready to earn some MP today?",
            "Nice try, but I can't write that paragraph for you!",
        ]

    print("=" * 60)
    print(f"  TTS TEST ({tts_engine.upper()})")
    print("=" * 60)

    for line in test_lines:
        print(f"\n  Speaking: \"{line}\"")
        tts.speak(line)
        time.sleep(0.5)

    print("\n  TTS test complete!")


def test_stt(config):
    """Test Whisper STT independently."""
    stt = SpeechToText(config)
    stt.initialize()

    print("=" * 60)
    print("  WHISPER STT TEST")
    print("=" * 60)

    ptt_key = config["audio"]["ptt_key"]
    print(f"\n  Press and hold [{ptt_key.upper()}] to record, release to transcribe.")
    print("  Press Ctrl+C to quit.\n")

    while True:
        try:
            wav_path = record_audio_ptt(config)
            if wav_path:
                text = stt.transcribe(wav_path)
                os.unlink(wav_path)
                if text:
                    print(f"  You said: \"{text}\"\n")
        except KeyboardInterrupt:
            print("\n  STT test complete!")
            break


def test_sfx(config):
    """Test sound effects generation (AudioGen local or ElevenLabs cloud)."""
    tts = TextToSpeech(config)
    tts.initialize()

    sfx_engine = tts.sfx_engine
    if sfx_engine != "audiogen" and tts.engine != "elevenlabs":
        print("[SFX] Sound effects require ElevenLabs or AudioGen engine.")
        print("[SFX] Set sfx_engine to 'audiogen' or tts_engine to 'elevenlabs'")
        return

    test_prompts = [
        ("Dramatic thunder crash with rain", 5),
        ("Sword being drawn from a sheath", 3),
        ("Crowd cheering in a medieval arena", 5),
    ]

    print("=" * 60)
    print(f"  SOUND EFFECTS TEST ({sfx_engine.upper()})")
    print("=" * 60)

    for prompt, duration in test_prompts:
        print(f"\n  Generating: \"{prompt}\" ({duration}s)")
        if sfx_engine == "audiogen":
            audio = tts.generate_sfx_audiogen(prompt, duration)
        else:
            audio = tts.generate_sound_effect(prompt, duration)
        if audio:
            play_audio(audio)
            try:
                os.unlink(audio)
            except OSError:
                pass
            time.sleep(0.5)
        else:
            print("  [FAILED] Could not generate sound effect")

    print("\n  Sound effects test complete!")


def test_music(config):
    """Test ElevenLabs music generation."""
    tts = TextToSpeech(config)
    tts.initialize()

    if tts.engine != "elevenlabs":
        print("[MUSIC] Music generation requires ElevenLabs engine.")
        print("[MUSIC] Set tts_engine to 'elevenlabs' in config/active-character.json")
        return

    character = config.get("_active_character", "hoggle")

    print("=" * 60)
    print("  MUSIC GENERATION TEST (ElevenLabs)")
    print("=" * 60)

    if character == "forte":
        prompt = (
            "Fantasy metal, shredding electric guitar riff, heavy and fast. "
            "Powerful female belting vocals singing a short rhyming couplet: "
            "'I swing my axe and strum my strings, "
            "a warrior princess who fights and sings!'"
        )
        duration_ms = 10000
        instrumental = False
    else:
        prompt = "Spooky playful chiptune melody with ghostly pig oinks"
        duration_ms = 10000
        instrumental = True

    print(f"\n  Generating: \"{prompt}\" ({duration_ms // 1000}s)")
    print("  (This may take 30-60 seconds...)\n")

    audio = tts.generate_music(prompt, duration_ms, instrumental=instrumental)
    if audio:
        print("  Playing...")
        play_audio(audio)
        try:
            os.unlink(audio)
        except OSError:
            pass
    else:
        print("  [FAILED] Could not generate music")

    print("\n  Music test complete!")


def list_audio_devices():
    """List available audio input/output devices."""
    print("=" * 60)
    print("  AUDIO DEVICES")
    print("=" * 60)
    print(sd.query_devices())
    print(f"\n  Default input:  {sd.query_devices(kind='input')['name']}")
    print(f"  Default output: {sd.query_devices(kind='output')['name']}")
    print()
    print("  TIP: Use --device <index> to select a mic, e.g.:")
    print("    python scripts/voice_pipeline.py --type --device 32")
    print("  Or set input_device in config/voice/voice-config.json")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Hoggle Voice Pipeline")
    parser.add_argument("--type", action="store_true", help="Type mode (keyboard input, TTS output)")
    parser.add_argument("--test-tts", action="store_true", help="Test TTS engine only")
    parser.add_argument("--test-stt", action="store_true", help="Test Whisper STT only")
    parser.add_argument("--test-sfx", action="store_true", help="Test ElevenLabs sound effects")
    parser.add_argument("--test-music", action="store_true", help="Test ElevenLabs music generation")
    parser.add_argument("--list-audio", action="store_true", help="List audio devices")
    parser.add_argument("--device", default=None,
                        help="Input device: index number or name substring (overrides config)")
    args = parser.parse_args()

    if args.list_audio:
        list_audio_devices()
        return

    config = load_config()

    # Apply --device override (CLI takes priority over config)
    if args.device is not None:
        config["audio"]["input_device"] = args.device

    if args.test_tts:
        test_tts(config)
    elif args.test_stt:
        test_stt(config)
    elif args.test_sfx:
        test_sfx(config)
    elif args.test_music:
        test_music(config)
    elif args.type:
        run_type_mode(config)
    else:
        run_voice_loop(config)


if __name__ == "__main__":
    main()
