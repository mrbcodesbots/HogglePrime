# 🐷👻 HogglePrime

**A locally-hosted AI classroom assistant for Millennial Tech Middle School**

Hoggle is a pig ghost from the Backrooms who got trapped at MTM when Mr. B accidentally downloaded a virus while looking at cute cat pictures. Now he's the unofficial mascot and AI teaching assistant for the Multimedia Heroes program.

## Features

- 🧠 **Local LLM** - Runs on Ollama with tiered intelligence (Quick/Normal/Deep)
- 🎤 **Voice Interface** - Talk to Hoggle, hear him respond (Whisper + Piper TTS)
- 💾 **Memory System** - Remembers conversations, daily summaries, student progress
- 🎮 **Multimedia Heroes Integration** - Awards MP, Timmy Coins, tracks achievements
- 👁️ **Face Recognition** - Greets opted-in students by name (privacy compliant)
- 🔒 **100% Local** - No student PII ever leaves the device
- 🎭 **Personality** - Fun, encouraging, middle-school appropriate character

## Quick Start

1. Install [Ollama](https://ollama.ai)
2. Install [Docker Desktop](https://docker.com)
3. Run `setup-hoggle-folders.bat`
4. Copy `.env.example` to `.env` and configure
5. Create the Hoggle models: see `/config/ollama-modelfiles/`

## Documentation

- `MASTERPLAN-HOGGLE.md` - Full project design and architecture
- `CLAUDE.md` - Development guidelines for AI assistants
- `prompts/hoggle-personality.md` - Hoggle's character system prompt

## Project Structure

```
HogglePrime/
├── prompts/              # System prompts
├── memories/             # Conversation and people memory
├── knowledge/            # RAG documents
├── n8n-workflows/        # Automation workflows
├── scripts/              # Python utilities
├── config/               # Model configurations
├── webapp/               # Web interfaces
└── logs/                 # Activity logs
```

## Privacy

- All processing happens locally
- Student data never leaves the machine
- Face recognition is opt-in only with parental consent
- Code names used for all external communications

## License

Private - Mr. B's classroom use only

---

*"Oink-credible learning awaits!"* - Hoggle
