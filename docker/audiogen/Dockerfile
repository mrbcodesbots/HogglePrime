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
RUN pip install --no-cache-dir \
    audiocraft \
    gradio \
    scipy

# Copy server app
COPY app.py .

EXPOSE 7861

CMD ["python", "app.py"]
