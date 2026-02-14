# AudioGen SFX Server
# Meta's AudioGen model (AudioCraft) served via Gradio API.
# Generates sound effects from text descriptions on GPU.
#
# Build:
#   docker build -t audiogen-server docker/audiogen/
#
# Run:
#   docker run --gpus all -p 7861:7861 --name audiogen audiogen-server
#
# The model downloads on first run (~2GB) and is cached in the container.
# To persist the cache across rebuilds, add a volume:
#   docker run --gpus all -p 7861:7861 -v audiogen_cache:/root/.cache --name audiogen audiogen-server

FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

WORKDIR /app

# Install system deps (pkg-config + libav*-dev needed to build PyAV from source)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
# audiocraft pins torch==2.1.0 which would downgrade the base image's 2.4.1
# and break NumPy/transformers, so install it --no-deps and add its
# requirements separately with versions compatible with torch 2.4.1.
# Note: xformers is NOT installed here -- it requires CUDA dev headers
# (absent in -runtime images) and pre-built wheels only live on PyTorch's
# own index.  app.py stubs it out; AudioGen inference doesn't need it.
RUN pip install --no-cache-dir --no-deps audiocraft && \
    pip install --no-cache-dir \
    av einops flashy "hydra-core>=1.1" hydra_colorlog julius \
    num2words sentencepiece "spacy>=3.6.1" huggingface_hub \
    "transformers>=4.31.0" demucs librosa torchmetrics encodec \
    protobuf torchaudio \
    gradio scipy

# Copy server app
COPY app.py .

EXPOSE 7861

CMD ["python", "app.py"]
