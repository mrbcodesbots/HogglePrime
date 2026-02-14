# MASTERPLAN: Project Hoggle 🐷👻
## A Local AI Classroom Assistant for Millennial Tech Middle School

**Version:** 1.0 (Planning Phase)  
**Created:** February 2026  
**Author:** Mr. B + Claude  
**Status:** Design Complete - Ready for Phased Implementation

---

## 🎯 Vision Statement

Hoggle is a locally-hosted AI classroom assistant with personality, voice, memory, and the ability to interact with classroom systems. He runs entirely on school hardware with no student PII leaving the device. He should feel like Jarvis - responsive, helpful, personable, and genuinely useful rather than gimmicky.

**Core Philosophy:** 
- Privacy first (100% local by default, optional API escalation)
- Modular architecture (each component can be built/tested independently)
- Personality matters (Hoggle should be memorable and fun)
- Practical utility (actually saves Mr. B time and engages students)

---

## 🖥️ Hardware Available

| Component | Specs | Role |
|-----------|-------|------|
| CPU | Intel i9-14900K | Whisper transcription, general processing |
| RAM | 64GB | Plenty for all services |
| GPU | NVIDIA RTX 4090 (24GB VRAM) | LLM inference, TTS |
| Storage | TBD - need SSD space | Models, memories, logs |
| Microphone | DJI Wireless Lavs (owned) + TBD clip mic | Voice input |
| Display | Classroom big screen via Mac laptop | Hoggle's "face" and interface |
| Network | Local only (no cloud required) | Privacy compliance |

### School PC Network Configuration

| Setting | Value |
|---------|-------|
| **Static IP** | 10.81.20.224 |
| **Default Gateway** | 10.81.20.1 |
| **Location** | MTM - Stays at school |

**Service URLs (from any device on school network):**
| Service | URL |
|---------|-----|
| Open WebUI (Hoggle Chat) | http://10.81.20.224:3000 |
| n8n (Workflows) | http://10.81.20.224:5678 |
| Ollama API | http://10.81.20.224:11434 |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLASSROOM ENVIRONMENT                            │
│                                                                             │
│   [Microphone] ──→ [Windows PC - "Hoggle's Brain"]                         │
│                           │                                                 │
│   [Webcam] ──────────────→│    ┌─────────────────────────────────────┐     │
│                           │    │         ORCHESTRATION LAYER         │     │
│                           │    │              (n8n)                  │     │
│                           │    │                                     │     │
│                           │    │  ┌─────────┐  ┌─────────────────┐  │     │
│                           │    │  │ Router  │  │ Action Executor │  │     │
│                           │    │  │(classify)│  │ (API calls)     │  │     │
│                           │    │  └────┬────┘  └────────┬────────┘  │     │
│                           │    └───────┼────────────────┼───────────┘     │
│                           │            │                │                  │
│                           │    ┌───────┴────────────────┴───────────┐     │
│                           │    │           LLM LAYER                │     │
│                           │    │            (Ollama)                │     │
│                           │    │                                     │     │
│                           │    │  ┌──────────┐ ┌────────┐ ┌───────┐ │     │
│                           │    │  │ Hoggle   │ │ Hoggle │ │Hoggle │ │     │
│                           │    │  │ Quick    │ │ Normal │ │ Deep  │ │     │
│                           │    │  │ (4K ctx) │ │(16K)   │ │(32K)  │ │     │
│                           │    │  └──────────┘ └────────┘ └───────┘ │     │
│                           │    └─────────────────────────────────────┘     │
│                           │                     │                          │
│                           │    ┌────────────────┴────────────────────┐     │
│                           │    │          MEMORY LAYER              │     │
│                           │    │                                     │     │
│                           │    │  ┌─────────┐ ┌───────┐ ┌─────────┐ │     │
│                           │    │  │ RAG/    │ │Daily  │ │ People  │ │     │
│                           │    │  │Knowledge│ │Memory │ │ Memory  │ │     │
│                           │    │  └─────────┘ └───────┘ └─────────┘ │     │
│                           │    └─────────────────────────────────────┘     │
│                           │                     │                          │
│                           │    ┌────────────────┴────────────────────┐     │
│                           │    │         INPUT/OUTPUT LAYER          │     │
│                           │    │                                     │     │
│                           │    │  ┌─────────┐ ┌───────┐ ┌─────────┐ │     │
│                           │    │  │ Whisper │ │ Piper │ │ OpenCV  │ │     │
│                           │    │  │ (STT)   │ │ (TTS) │ │ (Vision)│ │     │
│                           │    │  └─────────┘ └───────┘ └─────────┘ │     │
│                           │    └─────────────────────────────────────┘     │
│                           │                     │                          │
│                           └─────────────────────┼──────────────────────────┘
│                                                 │                          │
│   [Big Screen Display] ←────────────────────────┘                          │
│        (via Mac laptop browser)                                            │
│                                                                             │
│   [External APIs - Optional Escalation]                                    │
│        • Claude API (complex tasks)                                        │
│        • Google Apps Script (Multimedia Heroes)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 The Three Hoggles (Tiered Intelligence)

| Tier | Model | Context | VRAM | Speed | Use Case |
|------|-------|---------|------|-------|----------|
| **Hoggle Quick** | qwen2.5:14b | 4,096 | ~10GB | ⚡⚡⚡ <1s | Greetings, simple Q&A, banter |
| **Hoggle Normal** | qwen2.5:14b | 16,384 | ~14GB | ⚡⚡ 1-3s | Classroom help, explanations |
| **Hoggle Deep** | qwen2.5:14b | 32,768 | ~18GB | ⚡ 3-5s | Document analysis, RAG queries |
| **Hoggle + Claude** | Claude API | 200K | N/A | 🌐 5-10s | Complex coding, "above paygrade" |

**Routing Logic (handled by n8n):**
```
IF message is greeting/simple → Hoggle Quick
ELSE IF message mentions documents OR needs memory → Hoggle Deep  
ELSE IF message is about complex code OR Hoggle says "I'm not sure" → Claude API
ELSE → Hoggle Normal
```

---

## 💾 Memory Architecture

### Layer 1: Conversation Memory (Built-in)
- **What:** Current chat session history
- **Where:** Open WebUI
- **Duration:** Single conversation
- **Limit:** Context window size

### Layer 2: Daily Memory
- **What:** Summary of each day's key events, interactions, topics covered
- **Where:** JSON files organized by date (`/memories/daily/2026-02-03.json`)
- **Duration:** Persists indefinitely
- **How:** n8n scheduled job runs at end of day, sends conversation logs to Hoggle Deep for summarization
- **Format:**
```json
{
  "date": "2026-02-03",
  "period_1": {
    "topics": ["binary conversion", "Construct 3 events"],
    "notable_moments": ["Maria completed Binary Bandits Level 5"],
    "questions_asked": 12,
    "mood": "energetic"
  },
  "period_2": { ... }
}
```

### Layer 3: People Memory (Opt-in Students)
- **What:** Individual student profiles - interests, progress, interaction history
- **Where:** SQLite database or JSON files (`/memories/people/student_id.json`)
- **Duration:** School year
- **Privacy:** Only for students who opt-in with parental consent
- **Format:**
```json
{
  "student_id": "MTM2026_0042",
  "preferred_name": "Alex",
  "face_encoding": "[stored locally only]",
  "interests": ["game design", "pixel art"],
  "current_project": "platformer game in Construct 3",
  "interaction_count": 47,
  "last_seen": "2026-02-02",
  "notes": "Responds well to game design analogies",
  "mp_balance": 1250
}
```

### Layer 4: Knowledge Memory (RAG)
- **What:** Reference documents Hoggle can search
- **Where:** Open WebUI Knowledge Bases
- **Contents:**
  - Multimedia Heroes syllabus and rules
  - Construct 3 primer documents
  - Classroom procedures
  - Assignment rubrics
  - FAQ from past student questions

### Layer 5: Growth Memory (Learning Over Time)
- **What:** Log of successful/unsuccessful interactions for prompt refinement
- **Where:** Feedback log (`/memories/feedback/`)
- **How:** Mr. B can flag good/bad responses, system logs patterns
- **Use:** Periodic review to update system prompts and knowledge base

---

## 🎤 Voice System Design

### Input (Speech-to-Text)
```
Microphone → Audio Stream → Whisper.cpp → Text → n8n
```

**Activation Options:**
| Method | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| Wake Word ("Hey Hoggle") | Hands-free, natural | Always listening, false positives | Best for demos |
| Push-to-Talk (foot pedal) | Precise control, no false positives | Need hardware | Best for daily use |
| Push-to-Talk (keyboard) | No extra hardware | Hands occupied | Backup option |
| Always-on in bursts | Simple | Processing overhead | Not recommended |

**Recommended Setup:**
- Primary: USB foot pedal for PTT (~$15)
- Secondary: Keyboard hotkey (F13 or similar unused key)
- Demo mode: Wake word for showing off to visitors

### Output (Text-to-Speech)
```
Hoggle's response → Piper TTS → Audio → Speakers
```

**Voice Selection:**
- Piper has multiple voices - test for one that fits Hoggle's personality
- Slightly raspy/warm voice would match a friendly ghost pig
- Speed adjustable for classroom clarity

---

## 👁️ Vision System Design (Phase 4)

### Face Recognition (Opt-in Only)
```
Webcam → OpenCV → face_recognition library → Match against /memories/faces/
```

**Privacy Safeguards:**
- Camera processes frames locally, never saves video
- Only stores face encodings for opted-in students
- Parental consent form required
- Student can opt-out anytime (delete their encoding)
- No cloud services involved

**Functionality:**
- Recognize student approaching → Greet by name
- Track who asked questions for daily summary
- Enable personalized responses based on People Memory

### Object/Gesture Recognition (Future)
- Hand raise detection → Hoggle acknowledges
- Thumbs up/down → Feedback on responses
- QR code scanning → Quick student identification alternative

---

## 🔌 Integration Points

### Multimedia Heroes (Google Apps Script)
| Action | Trigger | API Call |
|--------|---------|----------|
| Award MP | "Hoggle, give Maria 10 points" | `POST /awardMP` |
| Check balance | "How many points does Alex have?" | `GET /getBalance` |
| Log achievement | "Maria completed Level 5" | `POST /logAchievement` |
| Get leaderboard | "Who's in the lead?" | `GET /leaderboard` |

### Classroom Display
| Action | Method |
|--------|--------|
| Show Hoggle's face/avatar | Web UI on big screen |
| Display student work | Open URL/file |
| Show timer | Web component |
| Celebration animation | Triggered overlay |

### Claude API (Escalation)
| Trigger | Action |
|---------|--------|
| Hoggle says "I'm not sure" | Forward to Claude |
| Code debugging request | Forward to Claude |
| Complex document analysis | Forward to Claude |
| Mr. B explicitly requests | Force Claude route |

---

## 📱 User Interfaces

### 1. Big Screen Display (Students See)
- Hoggle's animated avatar/face
- Current conversation (large text)
- Celebration effects when points awarded
- Timer/clock when needed

### 2. Teacher Dashboard (Mr. B's Mac)
- Full Open WebUI chat interface
- Quick action buttons (award points, switch modes)
- System status (which Hoggle tier active, memory usage)
- Daily summary view

### 3. Voice Interface (Primary Interaction)
- PTT activation
- Audio feedback from Piper TTS
- No screen required for basic interactions

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Hoggle can chat with personality through a web interface

- [ ] Create three Ollama models (quick/normal/deep)
- [ ] Configure Open WebUI with Hoggle persona
- [ ] Write and test system prompt
- [ ] Set up basic Knowledge Base (upload Multimedia Heroes docs)
- [ ] Test conversation quality and speed
- [ ] Create CLAUDE.md for development reference

**Success Criteria:** Can have a fun, in-character conversation with Hoggle in browser

### Phase 2: Voice (Week 3-4)
**Goal:** Talk to Hoggle, hear him respond

- [ ] Install and configure Whisper.cpp or faster-whisper
- [ ] Install and configure Piper TTS
- [ ] Select and customize Hoggle's voice
- [ ] Set up PTT system (foot pedal or keyboard)
- [ ] Create n8n workflow: Audio → STT → Hoggle → TTS → Audio
- [ ] Test voice conversation loop
- [ ] Optimize for latency (<3 second response time goal)

**Success Criteria:** Can speak to Hoggle and hear spoken response within 3 seconds

### Phase 3: Actions & Integration (Week 5-6)
**Goal:** Hoggle can actually DO things

- [ ] Design structured output format for commands
- [ ] Create n8n workflows for each action type
- [ ] Connect to Multimedia Heroes GAS APIs
- [ ] Implement smart routing between Hoggle tiers
- [ ] Add Claude API escalation path
- [ ] Test: "Hoggle, give Maria 10 points" → Actually awards points

**Success Criteria:** Voice command successfully awards MP through the system

### Phase 4: Memory & People (Week 7-8)
**Goal:** Hoggle remembers things and recognizes students

- [ ] Implement Daily Memory system (n8n scheduled job)
- [ ] Set up People Memory database structure
- [ ] Create opt-in consent workflow
- [ ] Install face_recognition library
- [ ] Set up webcam processing pipeline
- [ ] Test face enrollment and recognition
- [ ] Connect face recognition to People Memory

**Success Criteria:** Hoggle greets opted-in student by name when they approach

### Phase 5: Display & Polish (Week 9-10)
**Goal:** Hoggle has a visual presence and feels complete

- [ ] Design/find Hoggle avatar (animated pig ghost!)
- [ ] Create big screen display interface
- [ ] Add celebration animations for achievements
- [ ] Implement teacher dashboard
- [ ] Add status indicators and feedback
- [ ] Stress test full system
- [ ] Document everything

**Success Criteria:** Full Jarvis-like experience working in classroom

### Phase 6: Learning & Refinement (Ongoing)
**Goal:** Hoggle gets better over time

- [ ] Implement feedback logging system
- [ ] Create weekly review process
- [ ] Refine system prompts based on feedback
- [ ] Expand Knowledge Base with successful Q&A
- [ ] Tune routing logic based on real usage
- [ ] Share with other teachers (maybe?)

**Success Criteria:** Measurable improvement in response quality over time

---

## 💰 Budget Estimate

| Item | Cost | Status |
|------|------|--------|
| PC Hardware | $0 | Already have |
| RTX 4090 | $0 | Already have |
| DJI Mics | $0 | Already have |
| USB Foot Pedal | ~$15 | Need to purchase |
| Cheap USB Lavalier (backup) | ~$20 | Optional |
| Webcam (if needed) | ~$30-50 | May already have |
| Claude API credits | ~$5-20/month | For escalation only |
| **Total** | **~$35-85** | Plus optional API costs |

---

## ⚠️ Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Response too slow | Tune context sizes, use Quick tier more |
| Voice recognition errors | PTT reduces errors, train on Mr. B's voice |
| Students try to abuse/trick Hoggle | System prompt includes boundaries, logging |
| Privacy concerns | 100% local, opt-in only, parental consent |
| Hoggle says something inappropriate | Content filtering in system prompt, review logs |
| System crashes during class | Auto-restart services, fallback to basic chat |
| Model updates break things | Pin versions, test updates before deploying |

---

## 📚 Reference Documents

- `CLAUDE.md` - Development guidelines and AI assistant instructions
- `/prompts/hoggle-personality.md` - Full system prompt
- `/memories/` - All memory storage
- `/docs/multimedia-heroes/` - Curriculum documents for RAG
- `/n8n-workflows/` - Exported workflow configurations

---

## 🎉 Success Vision

**A day in the life with Hoggle:**

*8:00 AM - Mr. B arrives*
> "Good morning Hoggle!"
> "Morning Mr. B! Ready for another oink-credible day. You've got 7th grade first period - they were working on Binary Bandits yesterday."

*8:15 AM - Students arrive*
> Hoggle sees Maria approach: "Hey Maria! Ready to crush Level 6 today?"

*During class*
> Student: "Hoggle, I'm stuck on my game. The player keeps falling through the floor."
> Hoggle: "Sounds like a collision issue! Check if your player has the Platform behavior AND your floor has the Solid behavior. Both need to be set. Try that and let me know!"

*Student succeeds*
> Mr. B: "Hoggle, give Maria 15 MP for solving her collision problem independently."
> Hoggle: "Oink-credible work Maria! 15 MP heading your way. You're now at 1,265 total - closing in on that Silver rank!"
> *Celebration animation plays on big screen*

*Complex question*
> Student: "Why does my Construct 3 event sheet run the events in a weird order?"
> Hoggle: "That's getting into some advanced stuff about event execution order. Let me phone a friend..." 
> *Escalates to Claude, returns with detailed explanation*

*End of day*
> "Hoggle, how did today go?"
> "Good day! 23 student interactions, 4 escalations to Claude, 145 MP awarded. Maria and Alex both hit new personal bests. Tomorrow you might want to review collision detection - got 6 questions about it today."

---

*This is Hoggle. This is the goal. Let's build it.* 🐷👻
