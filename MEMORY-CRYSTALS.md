# Memory Crystals - Hoggle's Knowledge System

**Version:** 1.0
**Created:** February 2026
**Author:** Mr. B + Claude
**Status:** Phase 1 - Foundation

---

## What Are Memory Crystals?

Memory Crystals are structured JSON files that give Hoggle instant, accurate access to classroom knowledge. Instead of RAG (which chops documents into fragments and hopes to find the right one), crystals store **exact, structured data** that gets loaded directly into Hoggle's prompt.

Think of it like this:
- **RAG** = searching through a shredded filing cabinet
- **Memory Crystals** = labeled drawers with organized folders

---

## Why Crystals Instead of RAG?

| Problem with RAG | How Crystals Fix It |
|------------------|---------------------|
| Chunks destroy document structure | Full data preserved in JSON |
| Retrieves wrong fragments | Loads exactly what's needed |
| Standards get hallucinated | Exact standard codes stored |
| Embedding model required | No embedding - direct file read |
| Small docs work poorly | Perfect for small, structured data |
| Slow (embed + search + retrieve) | Fast (read file + inject) |

**When RAG IS still useful:** Searching through hundreds of pages where you don't know what you're looking for. For Hoggle's classroom use case (known documents, structured data), crystals are better.

---

## Crystal Types

### 1. Knowledge Crystals (curriculum, standards, assignments)
Structured reference data that doesn't change often.

```
crystals/
  knowledge/
    expression-week.json          # Assignment details + rubrics
    aed-career-standards.json     # CTE standards with codes
    multimedia-heroes-rules.json  # Program rules, MP system
    construct3-quick-ref.json     # Common Construct 3 help
```

### 2. Context Crystals (classroom state, schedule)
Data that changes daily or per-period.

```
crystals/
  context/
    today.json                    # Today's schedule, announcements
    current-unit.json             # What we're working on this week
    classroom-rules.json          # Procedures and expectations
```

### 3. Memory Crystals (student interactions, daily logs)
Data that grows over time. Maps to MASTERPLAN Layers 2-3.

```
crystals/
  memory/
    daily/
      2026-02-03.json             # Daily summary
      2026-02-04.json
    students/                     # Opt-in only, uses skeys
      skey_abc123.json            # Individual student profile
      skey_def456.json
```

### 4. Personality Crystals (Hoggle's character extras)
Fun facts, running jokes, seasonal content.

```
crystals/
  personality/
    hoggle-facts.json             # Random Hoggle lore
    class-inside-jokes.json       # Running jokes by period
    seasonal.json                 # Holiday/event-specific content
```

---

## Crystal Schema

Every crystal follows this format:

```json
{
  "crystal_id": "expression-week",
  "crystal_type": "knowledge",
  "version": 1,
  "created": "2026-02-03",
  "updated": "2026-02-03",
  "description": "Expression Week assignments, rubrics, and MP values",
  "tags": ["assignments", "expression", "mp", "rubrics"],
  "data": {
    // ... structured content specific to this crystal
  }
}
```

### Required Fields
| Field | Type | Description |
|-------|------|-------------|
| `crystal_id` | string | Unique identifier (kebab-case) |
| `crystal_type` | string | `knowledge`, `context`, `memory`, `personality` |
| `version` | number | Increment when content changes |
| `created` | string | ISO date |
| `updated` | string | ISO date of last modification |
| `description` | string | What this crystal contains |
| `tags` | array | Keywords for routing (used by n8n) |
| `data` | object | The actual structured content |

---

## How It Works (n8n Flow)

```
Student asks question
     |
     v
[n8n Webhook receives message]
     |
     v
[Keyword Router] --- matches tags from crystal index
     |
     v
[Crystal Loader] --- reads matching crystal JSON file(s)
     |
     v
[Prompt Builder] --- injects crystal data into system prompt
     |
     v
[Gemini Flash API] --- generates response with full context
     |
     v
[Response returned to student]
```

### Crystal Index

A master index file tells n8n which crystals to load for which topics:

```json
{
  "index": [
    {
      "crystal_id": "expression-week",
      "tags": ["expression", "assignments", "drawing", "song", "comic", "game", "film", "mp"],
      "path": "crystals/knowledge/expression-week.json",
      "load_for": ["What are the assignments", "expression week", "how many MP"]
    },
    {
      "crystal_id": "aed-career-standards",
      "tags": ["standards", "AED", "career", "cluster", "CTE", "pathway"],
      "path": "crystals/knowledge/aed-career-standards.json",
      "load_for": ["what standard", "which standards", "CTE", "career cluster"]
    }
  ]
}
```

### Multi-Crystal Loading

When Mr. B asks "connect Expression Week assignments to AED standards," n8n loads BOTH crystals and injects them together. The model gets:
- All 12 assignments with rubrics
- All relevant standards with codes
- Can make accurate connections because it has ALL the data

---

## n8n Workflow Design

### Updated Keyword Router

Extends the existing `hoggle-keyword-router` workflow:

```
[Webhook] → [Check Crystal Index] → [Load Matching Crystals]
                                          |
                                    [Build Prompt with Crystal Data]
                                          |
                                    [Send to Gemini Flash]
                                          |
                                    [Return Response]
```

### Crystal Loading Logic (n8n Code Node)

```javascript
// Pseudocode for n8n Function node
const message = $input.item.json.body.message.toLowerCase();
const index = JSON.parse(fs.readFileSync('crystals/crystal-index.json'));

// Find matching crystals based on tags
const matchedCrystals = index.index.filter(crystal => {
  return crystal.tags.some(tag => message.includes(tag));
});

// Load crystal data
const crystalData = matchedCrystals.map(crystal => {
  return JSON.parse(fs.readFileSync(crystal.path));
});

// Build enhanced prompt
const systemPrompt = baseHogglePrompt + "\n\n## KNOWLEDGE AVAILABLE:\n" +
  crystalData.map(c => JSON.stringify(c.data, null, 2)).join("\n\n");

return { systemPrompt, crystalData, message };
```

---

## Implementation Plan

### Phase A: Convert Existing Docs to Crystals (Now)
1. Convert Expression Week PDF → `expression-week.json`
2. Convert AED Career Standards → `aed-career-standards.json`
3. Create `crystal-index.json`
4. Create Multimedia Heroes rules crystal
5. Test loading crystals manually

### Phase B: n8n Crystal Loader (Next)
1. Create "Crystal Loader" n8n workflow
2. Add crystal index lookup node
3. Add file read node for crystal loading
4. Update prompt builder to inject crystal data
5. Test end-to-end: question → crystal load → accurate answer

### Phase C: Context Crystals (After)
1. Create `today.json` template
2. n8n scheduled job to update daily context
3. Create `current-unit.json` for weekly updates
4. Teacher dashboard to edit context crystals (future)

### Phase D: Memory Crystals (Phase 4 of MASTERPLAN)
1. Design student memory crystal schema
2. Create n8n workflow for saving interactions
3. Implement "Hoggle, remember..." voice commands
4. Connect to skey system for privacy

---

## Privacy Rules (Same as MASTERPLAN)

- **Knowledge crystals:** No student PII. Standards, assignments, rules only.
- **Context crystals:** No student names. "Period 3 is working on platformers."
- **Memory crystals:** Uses skeys only. No real names in JSON files.
- **All crystals stay local.** Never transmitted to cloud APIs.
- **Gemini Flash receives crystal DATA, not student identifiers.**

---

## Relationship to MASTERPLAN

Memory Crystals map to the existing MASTERPLAN memory layers:

| MASTERPLAN Layer | Crystal Equivalent |
|-----------------|-------------------|
| Layer 1: Conversation Memory | Still handled by Open WebUI |
| Layer 2: Daily Memory | `crystals/memory/daily/` |
| Layer 3: People Memory | `crystals/memory/students/` |
| Layer 4: Knowledge Memory (RAG) | **REPLACED by** `crystals/knowledge/` |
| Layer 5: Growth Memory | `crystals/memory/feedback/` (future) |

The key change: Layer 4 moves from RAG to structured crystals. Everything else stays the same.

---

## File Size Considerations

Gemini Flash context window: 1,048,576 tokens (1M)

Typical crystal sizes:
- Expression Week (12 assignments): ~4,000 tokens
- AED Standards (full document): ~15,000 tokens
- Daily context: ~500 tokens
- Student profile: ~200 tokens

**Loading 5 crystals at once: ~20,000 tokens = 2% of context window.**

You have massive headroom. No chunking needed.

---

*Memory Crystals: Because Hoggle deserves organized knowledge, not shredded documents.*
