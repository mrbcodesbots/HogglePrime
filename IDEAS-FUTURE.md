# Future Ideas for Hoggle

**Captured:** February 2026
**Source:** Brainstorm session with Claude

These ideas expand on the MASTERPLAN. Add to appropriate phases when implementing.

---

## Voice Reminders That Speak Aloud (Phase 2-3)

**Idea:** Scheduled reminders where Hoggle actually speaks unprompted.

**Examples:**
- "5 minutes until the bell, save your work!"
- "Period 3, don't forget your binary worksheet is due tomorrow!"
- Custom reminders Mr. B sets: "Hoggle, remind me in 10 minutes to check on table 4"

**Implementation:**
- n8n Schedule Trigger node for fixed times
- n8n Delay node for "remind me in X minutes"
- Both trigger Piper TTS → Speakers
- Could pull context from daily schedule JSON

---

## Sound Bank for Personality (Phase 2-5)

**Idea:** Pre-recorded or generated sound effects that make Hoggle feel alive.

**Possible sounds:**
- Idle oinks/snorts (plays randomly when quiet)
- Thinking sounds ("hmm", pig snuffling)
- Celebration sounds (for MP awards)
- Error/confused sounds
- Greeting flourishes
- Drumroll before announcements

**Implementation:**
- Folder: `/sounds/hoggle/`
- n8n or webapp triggers audio playback
- Could layer with TTS or play standalone
- Consider: commission voice actor? AI generate? Find CC-licensed?

---

## Simple PTT Webapp (Phase 2)

**Idea:** Browser-based control panel instead of just keyboard/footpedal.

**Features:**
- Big "Hold to Talk" button
- Quick command buttons (Attention!, 5 min timer, etc.)
- Status display (which Hoggle tier active, listening state)
- Volume/mute controls
- Mobile-friendly for Mr. B's phone?

**Implementation:**
- Single HTML file with JavaScript
- Calls n8n webhooks
- Runs in browser on Mr. B's Mac
- Could expand to full teacher dashboard later

---

## Voice-Triggered Memory Saves (Phase 3-4)

**Idea:** Natural voice commands to save information.

**Examples:**
- "Hoggle, remember that Maria is stuck on jump physics"
- "Hoggle, note that we stopped at slide 15"
- "Hoggle, Alex was absent today"

**Implementation:**
- Router detects "remember" or "note" keywords
- Parses entity (student name) and information
- Saves to appropriate memory file
- Confirms: "Got it! I'll remember Maria is stuck on jump physics."

---

## Personality Shaping Through Conversation (Phase 6)

**Idea:** Hoggle's personality evolves based on interactions.

**Approaches:**
1. **Simple:** `personality-notes.md` file that Mr. B edits, appends to system prompt
2. **Medium:** Hoggle suggests additions: "Should I remember that Period 3 likes being called the chaos crew?"
3. **Advanced:** Fine-tune model on conversation logs (significant effort)

**Start with #1**, graduate to #2 when comfortable.

---

## Classroom Printer Rivalry (Fun)

**Idea:** Hoggle has a running joke rivalry with the classroom printer.

- Blames printer for problems
- Celebrates when printer works
- Makes snide comments about paper jams
- Could actually monitor printer status via network?

---

*Add more ideas here as they come up!*
