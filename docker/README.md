# Docker Services for Hoggle

Local AI services that run on the RTX 4090 via Docker with GPU access.

## Prerequisites

- Docker Desktop installed with WSL2 backend
- NVIDIA Container Toolkit (comes with Docker Desktop on Windows)
- RTX 4090 (or any NVIDIA GPU with enough VRAM)

## Services

### ACE-Step 1.5 (Music Generation) — Port 7860

Local music generation with voice cloning. Pre-built Docker image.

```bash
docker run -d --gpus all -p 7860:7860 --name acestep --restart unless-stopped ghcr.io/dotnetautor/ace-step-1.5-docker:latest
```

- **UI:** http://localhost:7860
- **API:** http://localhost:7860/api/generate
- **VRAM:** ~4GB
- **Config:** Set `music_engine` to `"acestep"` in `config/active-character.json`

### AudioGen (Sound Effects) — Port 7861

Local sound effects generation using Meta's AudioGen model.

**Build (one time):**
```bash
docker build -t audiogen-server docker/audiogen/
```

**Run:**
```bash
docker run -d --gpus all -p 7861:7861 -v audiogen_cache:/root/.cache --name audiogen --restart unless-stopped audiogen-server
```

- **UI:** http://localhost:7861
- **API:** http://localhost:7861/api/generate
- **VRAM:** ~4GB
- **Config:** Set `sfx_engine` to `"audiogen"` in `config/active-character.json`

The model (~2GB) downloads on first run. The `-v audiogen_cache` volume caches it so
rebuilds don't re-download.

## Managing Services

```bash
# Check running containers
docker ps

# View logs
docker logs acestep
docker logs audiogen

# Stop/start
docker stop acestep audiogen
docker start acestep audiogen

# Remove and recreate (if needed)
docker rm -f acestep audiogen
# Then re-run the docker run commands above
```

## VRAM Usage

Both services together use ~8GB VRAM, leaving ~16GB free on the RTX 4090 for
Whisper, Chatterbox, and other local models.

| Service | VRAM | Port |
|---------|------|------|
| ACE-Step 1.5 | ~4GB | 7860 |
| AudioGen | ~4GB | 7861 |
| Whisper large-v3-turbo | ~6GB | (in-process) |
| **Total** | **~14GB** | |
