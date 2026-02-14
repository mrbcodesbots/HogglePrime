# CLAUDE.md - Project Hoggle Development Guide
## Instructions for AI Assistants (Claude, etc.)

**Last Updated:** February 2026  
**Project:** Hoggle - Local AI Classroom Assistant  
**Owner:** Mr. B (Media Arts Teacher, Millennial Tech Middle School)

---

## 🎯 What Is This Project?

Hoggle is a locally-hosted AI classroom assistant being built for a Title I middle school in San Diego. The goal is a "Jarvis-like" experience that:

- Runs 100% locally on school hardware (privacy compliant - no student PII leaves the device)
- Has a fun personality (Hoggle is a pig ghost from the Backrooms who got stuck at the school)
- Can speak and listen (voice interface)
- Connects to classroom systems (award points, track progress)
- Remembers students and context over time
- Recognizes faces (opt-in only with parental consent)

**This is an ambitious project being built modularly by a teacher who is a GUI-oriented user, not a terminal expert.**

---

## 🖥️ Technical Environment

### Hardware
| Component | Specs |
|-----------|-------|
| CPU | Intel i9-14900K |
| RAM | 64GB |
| GPU | NVIDIA RTX 4090 (24GB VRAM) |
| OS | Windows 11 |

### Software Stack
| Tool | Purpose | Status |
|------|---------|--------|
| Ollama | LLM inference | ✅ Installed |
| Open WebUI | Chat interface | ✅ Installed |
| Docker Desktop | Container runtime | ✅ Installed |
| n8n | Workflow orchestration | ✅ Installed (needs configuration) |
| Python | Scripts and integrations | ✅ Installed (version TBD) |
| Whisper | Speech-to-text | 🔲 Not yet installed |
| Piper TTS | Text-to-speech | 🔲 Not yet installed |
| face_recognition | Facial recognition | 🔲 Not yet installed |

### Ollama Models
| Model | Context | Purpose |
|-------|---------|---------|
| `hoggle-quick` | 4,096 | Fast greetings, simple Q&A |
| `hoggle-normal` | 16,384 | Standard classroom help |
| `hoggle-deep` | 32,768 | Document analysis, RAG |

Base model: `qwen2.5:14b-instruct`

---

## 👨‍🏫 About Mr. B (The User)

### Technical Comfort
- **Strengths:** Creative problem-solving, game design (Construct 3), Google Apps Script, curriculum development, has built complex systems before
- **Challenges:** Terminal/command-line work, prefers GUI solutions, may need step-by-step instructions for unfamiliar tools
- **Approach:** Willing to do things right rather than rush, appreciates understanding WHY not just HOW

### Teaching Context
- Subject: Media Arts (game development, video production, music, digital art)
- Grades: 7th and 8th grade
- School: Title I school in San Diego with diverse, multilingual student population (Spanish, Vietnamese, Haitian Creole)
- Curriculum: "Multimedia Heroes" - gamified learning with MP (Multimedia Points) and skill progression

### When Helping Mr. B
- Explain terminal commands but offer GUI alternatives when possible
- Be thorough - he prefers understanding the system over quick fixes
- Reference his existing knowledge (Construct 3, GAS) for analogies
- Remember he's building this to actually use in a classroom with real students

---

## 📁 Project Structure

```
C:\Users\jason\Documents\HogglePrime\    (Home PC)
C:\Users\[username]\Documents\HogglePrime\   (School PC - adjust username)
├── MASTERPLAN-HOGGLE.md     # Full project design document
├── CLAUDE.md                 # This file - AI assistant guidelines
├── prompts/
│   └── hoggle-personality.md # System prompt for Hoggle
├── memories/
│   ├── daily/               # Daily summary JSON files
│   ├── people/              # Student profiles (opt-in)
│   └── feedback/            # Interaction feedback logs
├── knowledge/               # Documents for RAG
│   ├── multimedia-heroes/
│   ├── construct3/
│   └── classroom/
├── n8n-workflows/           # Exported n8n configurations
├── scripts/                 # Python utilities
│   ├── face_enrollment.py
│   ├── voice_pipeline.py
│   └── memory_manager.py
└── config/
    └── ollama-modelfiles/   # Modelfile definitions for each tier
```

---

## 🚨 Important Constraints

### Privacy (NON-NEGOTIABLE)
- **No student PII can leave the local machine** - no cloud APIs that receive student names, faces, or data
- Claude API escalation only sends the QUESTION, never student identifiers
- Face encodings stored locally only, never transmitted
- All student-related features require documented parental consent

### Performance
- Classroom interactions need to feel conversational (<3 second response time)
- Use the appropriate Hoggle tier - don't default to Deep for simple queries
- Monitor VRAM usage - stay within 24GB to avoid CPU spillover

### Safety
- Hoggle's system prompt includes boundaries for appropriate school content
- Logging enabled for all interactions (Mr. B can review)
- Hoggle should never pretend to be a real authority figure or give medical/legal advice

---

## 🔧 Common Development Tasks

### Adding to Knowledge Base
1. Place documents in appropriate `/knowledge/` subfolder
2. Upload to Open WebUI: Workspace → Knowledge → Add to collection
3. Test retrieval with relevant questions

### Updating Hoggle's Personality
1. Edit `/prompts/hoggle-personality.md`
2. Copy to Open WebUI: Workspace → Models → Hoggle → Edit → System Prompt
3. Test in conversation

### Creating n8n Workflows
1. Design workflow in n8n visual editor
2. Export JSON backup to `/n8n-workflows/`
3. Document webhook URLs and triggers

### Modifying Ollama Models
1. Edit appropriate modelfile in `/config/ollama-modelfiles/`
2. Run: `ollama create <model-name> -f <modelfile-path>`
3. Test in Open WebUI

---

## 🚀 Deploying n8n Workflow Updates from Git

When Claude (or anyone) pushes workflow changes to the repo, here's how to deploy them on the school PC:

### Step 1: Pull Latest Code
- **GitHub Desktop:** Fetch origin → Pull origin (make sure you're on the right branch)
- **Terminal:** `cd C:\Users\jason\Documents\HogglePrimeHome && git pull origin claude/sync-roster-lookup-zcOgf`

### Step 2: Import/Update Workflows in n8n

**For UPDATED workflows** (e.g., crystal loader got new nodes):
1. Open n8n at http://localhost:5678
2. Open the existing workflow
3. Select all nodes (Ctrl+A) → Delete
4. Click **...** menu (top right) → **Import from File**
5. Browse to the workflow JSON (files are at `/data/n8n-workflows/` inside the container, which maps to `C:\Users\jason\Documents\HogglePrimeHome\n8n-workflows\` on Windows)
6. **Re-attach credentials**: Any HTTP Request node that calls Gemini needs the "Gemini API Key" Header Auth credential re-selected (click the node → set credential)
7. Save and activate

**For NEW workflows:**
1. n8n home screen → **Add Workflow** (or + button)
2. Click **...** menu → **Import from File**
3. Browse to the new workflow JSON
4. Set credentials on any nodes that need them
5. Save and activate

### Step 3: Test with curl

All Hoggle webhooks accept POST with JSON body. Test from PowerShell or terminal:

```bash
# Test crystal loader (main Hoggle chat)
curl -X POST http://localhost:5678/webhook/hoggle-crystal -H "Content-Type: application/json" -d "{\"message\": \"Hey Hoggle!\"}"

# Test mode switcher (change behavior mode)
curl -X POST http://localhost:5678/webhook/hoggle-mode -H "Content-Type: application/json" -d "{\"mode\": \"demo\"}"

# Test roster sync (on-demand, requires GAS endpoint configured)
curl -X POST http://localhost:5678/webhook/hoggle-roster-sync
```

### Current Workflow Inventory

| Workflow File | Webhook Path | Purpose | Credentials Needed |
|---|---|---|---|
| `hoggle-crystal-loader.json` | POST `/webhook/hoggle-crystal` | Main chat pipeline (crystals + bouncer + Gemini) | Gemini API Key (on **Classify Intent** AND **Send to Gemini** nodes) |
| `hoggle-mode-switcher.json` | POST `/webhook/hoggle-mode` | Switch behavior modes (classroom/demo/district/hype/gaming) | None (local file I/O only) |
| `hoggle-roster-sync.json` | POST `/webhook/hoggle-roster-sync` + 30-min schedule | Sync student roster from GAS to local cache | None (but needs GAS URL configured in node) |

### n8n Docker Reference
If the container needs to be recreated:
```bash
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n -v "C:\Users\jason\Documents\HogglePrimeHome":/data --add-host=host.docker.internal:host-gateway -e NODE_FUNCTION_ALLOW_BUILTIN=fs,path --restart always n8nio/n8n
```

---

## 🐷 Hoggle's Character (For Reference)

**Backstory:** Hoggle was a pig ghost roaming the Backrooms until Mr. B accidentally downloaded a computer virus while looking at cute cat pictures. The virus opened a digital portal and Hoggle got pulled through, binding him to MTM's network. He was confused at first but now loves the school and considers himself the unofficial mascot.

**Personality Traits:**
- Warm, encouraging, slightly mischievous
- Makes occasional pig puns (but not excessively)
- Speaks at middle school level - not condescending, not overly complex
- Gets genuinely excited about student creativity
- Honest about his limitations ("I'm just a pig ghost, better ask Mr. B about that!")
- Playful rivalry with computer viruses

**Voice:** Should sound warm, slightly raspy, friendly - not robotic, not overly energetic

**Boundaries:**
- Won't do students' work for them (guides, doesn't give answers)
- Escalates complex technical questions rather than guessing
- Keeps content school-appropriate at all times
- Doesn't pretend to have authority he doesn't have

---

## 📋 Current Phase & Status

**Phase 1: Foundation** ← CURRENT
- [x] Ollama installed
- [x] Open WebUI installed  
- [x] Model selected (qwen2.5:14b-instruct)
- [x] Context length configured (16,384)
- [ ] Three-tier models created (quick/normal/deep)
- [ ] System prompt finalized and tested
- [ ] Knowledge base populated
- [ ] CLAUDE.md completed ← IN PROGRESS

**Next Steps:**
1. Create the three Ollama modelfiles
2. Test Hoggle persona in Open WebUI
3. Upload Multimedia Heroes docs to knowledge base
4. Begin Phase 2 (Voice) planning

---

## 💡 Useful Commands Reference

### Ollama
```bash
# List installed models
ollama list

# Run a model interactively
ollama run qwen2.5:14b-instruct

# Create model from modelfile
ollama create hoggle-normal -f modelfile.txt

# Show model details
ollama show qwen2.5:14b-instruct

# Check Ollama version
ollama --version
```

### Docker
```bash
# List running containers
docker ps

# View container logs
docker logs open-webui

# Restart a container
docker restart open-webui

# Stop a container
docker stop open-webui
```

### n8n
```bash
# n8n runs in Docker, access at:
# http://localhost:5678 (or whatever port configured)
```

---

## 🤝 How to Help on This Project

When Mr. B asks for help with Hoggle:

1. **Check the MASTERPLAN** - The architecture and phases are documented
2. **Respect the constraints** - Privacy, performance, safety
3. **Prefer GUI solutions** - But explain CLI when necessary
4. **Be modular** - Each component should work independently
5. **Test before deploying** - This will be used in a real classroom
6. **Document changes** - Update relevant files when making modifications

When something is "above Hoggle's paygrade" in the actual system, it escalates to Claude. The irony is not lost on us. 🐷

---

## 📞 External Integrations

### Multimedia Heroes (Google Apps Script)
- Mr. B has existing GAS APIs for the point system
- Hoggle will call these via n8n HTTP requests
- Endpoints TBD - Mr. B to provide

### Claude API (Escalation)
- Used for complex coding questions, debugging
- Hoggle frames the question, removes student identifiers
- Response comes back through Hoggle's voice

### Future Possibilities
- OBS integration for streaming/recording
- Home Assistant for classroom IoT
- Discord bot version for remote students?

---

*This document should be updated as the project evolves. When in doubt, check MASTERPLAN-HOGGLE.md for the full vision.*
