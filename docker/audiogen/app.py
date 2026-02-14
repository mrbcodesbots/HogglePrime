"""
AudioGen SFX Server
====================
Gradio-based API server for Meta's AudioGen model (from AudioCraft).
Generates sound effects from text descriptions.

Runs inside Docker with GPU access. Serves on port 7861.

API endpoint: POST /api/generate
    Input:  {"data": ["thunder crash with rain", 5.0]}
    Output: {"data": [{"name": "/tmp/xxx.wav", ...}]}

Also accessible via Gradio UI at http://localhost:7861
"""

import os
import sys
import tempfile
import types

# Stub out xformers before audiocraft tries to import it.
# AudioCraft unconditionally does "from xformers import ops" in its
# transformer module and calls _verify_xformers_memory_efficient_compat()
# which checks for specific functions.  xformers is only used for
# memory-efficient attention during training.  For inference the standard
# PyTorch attention path works fine, so we provide a stub with the
# attributes audiocraft expects instead of pulling in the full xformers
# build (which needs CUDA dev headers).
_xformers = types.ModuleType("xformers")
_ops = types.ModuleType("xformers.ops")

# audiocraft's _verify_xformers_memory_efficient_compat() imports these:
_ops.memory_efficient_attention = None
_ops.LowerTriangularMask = None

_xformers.ops = _ops
sys.modules["xformers"] = _xformers
sys.modules["xformers.ops"] = _ops

import gradio as gr
import scipy.io.wavfile
import torch

# Patch audiocraft's transformer module to bypass xformers entirely.
# Three things are needed:
#   1. The stub above satisfies "from xformers import ops" at module level.
#   2. Replace _verify_xformers_memory_efficient_compat() with a no-op so
#      StreamingMultiheadAttention.__init__ doesn't raise ImportError.
#   3. Force _efficient_attention_backend = 'torch' so the forward() method
#      uses PyTorch's scaled_dot_product_attention instead of xformers ops.
import audiocraft.modules.transformer as _ac_tx
_ac_tx._verify_xformers_memory_efficient_compat = lambda: None
if hasattr(_ac_tx, '_efficient_attention_backend'):
    _ac_tx._efficient_attention_backend = 'torch'

from audiocraft.models import AudioGen


# Load model once at startup
MODEL_NAME = os.environ.get("AUDIOGEN_MODEL", "facebook/audiogen-medium")
print(f"[AudioGen] Loading model: {MODEL_NAME}")
model = AudioGen.get_pretrained(MODEL_NAME)
print(f"[AudioGen] Model loaded on {model.device}")
print(f"[AudioGen] Sample rate: {model.sample_rate}")


def generate_sfx(prompt: str, duration: float = 5.0) -> str:
    """Generate a sound effect from a text prompt.

    Args:
        prompt: Text description of the sound (e.g. "dramatic thunder crash").
        duration: Duration in seconds (0.5-30). Default 5.

    Returns:
        Path to generated WAV file.
    """
    duration = max(0.5, min(30.0, float(duration)))
    print(f"[AudioGen] Generating: \"{prompt}\" ({duration}s)")

    model.set_generation_params(duration=duration)
    wav = model.generate([prompt])

    # wav is a torch tensor [batch, channels, samples]
    audio = wav[0].cpu().numpy()
    if audio.ndim > 1:
        audio = audio[0]  # take first channel if multi-channel

    # Normalize to prevent clipping
    peak = max(abs(audio.max()), abs(audio.min()))
    if peak > 0:
        audio = audio / peak * 0.95

    # Save to temp WAV
    output_path = tempfile.mktemp(suffix=".wav")
    scipy.io.wavfile.write(output_path, model.sample_rate, audio)
    print(f"[AudioGen] Saved: {output_path}")
    return output_path


# Build Gradio interface
demo = gr.Interface(
    fn=generate_sfx,
    inputs=[
        gr.Textbox(label="Sound Description", placeholder="dramatic thunder crash with rain"),
        gr.Slider(minimum=0.5, maximum=30.0, value=5.0, step=0.5, label="Duration (seconds)"),
    ],
    outputs=gr.Audio(label="Generated Sound Effect", type="filepath"),
    title="AudioGen SFX Server",
    description="Generate sound effects from text descriptions using Meta's AudioGen model.",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
