# How to Crystalize - Converting Documents to Memory Crystals

**For:** Mr. B, Claude, or any AI assistant working on Project Hoggle
**Purpose:** Step-by-step guide to convert any PDF/document into a structured Memory Crystal JSON file

---

## What Is Crystalizing?

Taking an unstructured document (PDF, Google Doc, handout) and converting it into a structured JSON file that Hoggle can read perfectly every time. No RAG, no chunking, no hallucination.

---

## Step 1: Identify the Crystal Type

| If the document is... | Crystal type | Folder |
|-----------------------|-------------|--------|
| Curriculum, standards, rubrics | `knowledge` | `crystals/knowledge/` |
| Schedule, announcements, daily info | `context` | `crystals/context/` |
| Student interaction logs | `memory` | `crystals/memory/` |
| Hoggle lore, jokes, personality | `personality` | `crystals/personality/` |

---

## Step 2: Read the Document and Identify Structure

Before writing JSON, read the entire document and identify:
- **What are the main sections?**
- **Is there a table or list?** → becomes an array
- **Are there categories/groups?** → becomes nested objects
- **Are there codes/numbers?** → preserve exactly (standard codes, MP values, etc.)
- **What would someone search for?** → becomes tags

---

## Step 3: Create the Crystal JSON

Use this template:

```json
{
  "crystal_id": "KEBAB-CASE-NAME",
  "crystal_type": "knowledge",
  "version": 1,
  "created": "YYYY-MM-DD",
  "updated": "YYYY-MM-DD",
  "description": "One sentence describing what this crystal contains",
  "tags": ["keyword1", "keyword2", "keyword3"],
  "data": {

  }
}
```

### Rules for the `data` field:
- **Preserve exact values** - standard codes, MP values, dates, names
- **Use arrays for lists** - assignments, achievements, standards
- **Use objects for grouped data** - categories, sections, periods
- **Keep descriptions short but complete** - enough for the model to answer questions
- **No student PII** - ever

---

## Step 4: Add Tags for Routing

Tags determine when n8n loads this crystal. Think: "What words would someone use when asking about this?"

**Good tags:** specific nouns, topic names, unique terms
```json
"tags": ["expression", "week", "drawing", "song", "comic", "film", "amv"]
```

**Bad tags:** generic words that match everything
```json
"tags": ["the", "what", "help", "school", "class"]
```

---

## Step 5: Update the Crystal Index

Add your new crystal to `crystals/crystal-index.json`:

```json
{
  "crystal_id": "your-crystal-id",
  "crystal_type": "knowledge",
  "path": "crystals/knowledge/your-crystal-id.json",
  "tags": ["your", "tags", "here"],
  "description": "What this crystal contains",
  "always_load": false
}
```

Set `always_load: true` only for context crystals that should be included in every conversation (like `today.json`).

---

## Step 6: Test

Ask Hoggle a question that should trigger this crystal. Check:
- [ ] Did n8n load the right crystal?
- [ ] Did Hoggle cite exact information from the crystal?
- [ ] Did Hoggle avoid hallucinating additional info?

---

## Examples of Good Crystalizing

### Example A: Assignment Document → Crystal

**Original PDF content:**
```
Assignment 1: "What I Love" Drawing
Topic: Express Drawz | Max MP: 40
Draw something meaningful to you...
Achievements:
- Canvas Ready (3 MP)
- Subject Present (5 MP)
```

**Crystalized:**
```json
{
  "number": 1,
  "topic": "Express Drawz",
  "name": "What I Love Drawing",
  "max_mp": 40,
  "description": "Draw something meaningful to you - a character, hobby, family member, pet, or anything you care about.",
  "achievements": [
    {"name": "Canvas Ready", "mp": 3, "description": "Artwork on uncrumpled paper with name on back"},
    {"name": "Subject Present", "mp": 5, "description": "Main subject clearly depicted and recognizable"}
  ]
}
```

### Example B: Standards Document → Crystal

**Original PDF content:**
```
AV.1.1 - Analyze and apply artistic processes
AV.1.2 - Demonstrate technical proficiency in audio/video
AV.2.1 - Evaluate media for quality and effectiveness
```

**Crystalized:**
```json
{
  "pathway": "Audio/Visual Technology",
  "standards": [
    {"code": "AV.1.1", "description": "Analyze and apply artistic processes", "category": "Creation"},
    {"code": "AV.1.2", "description": "Demonstrate technical proficiency in audio/video", "category": "Creation"},
    {"code": "AV.2.1", "description": "Evaluate media for quality and effectiveness", "category": "Evaluation"}
  ]
}
```

### Example C: Daily Context → Crystal

```json
{
  "date": "2026-02-05",
  "day_of_week": "Wednesday",
  "current_event": "Expression Week",
  "announcements": ["Expression Week runs Feb 3-7", "Goal: earn at least 100 MP"],
  "periods": {
    "period_1": {"grade": "7th", "focus": "Expression Week assignments"},
    "period_3": {"grade": "8th", "focus": "Expression Week assignments"}
  }
}
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Paraphrasing content | Copy exact wording, codes, and numbers |
| Missing achievements/rubric details | Include every line item with MP values |
| Tags too generic | Use specific nouns from the document |
| Forgetting to update crystal-index.json | Always add new crystals to the index |
| Including student names | Use skeys only, never real names |
| Making one giant crystal | Split into logical topics (one per unit/event) |

---

## File Size Guidelines

| Document Size | Approach |
|---------------|----------|
| 1-20 pages | Single crystal with full detail |
| 20-50 pages | Split into 2-3 crystals by section |
| 50+ pages | Split by chapter/topic, one crystal each |

Gemini Flash has 1M token context. A typical crystal is 2,000-15,000 tokens. You have massive headroom - don't over-compress.

---

## Crystal Maintenance

- **Update `version` field** when you modify crystal content
- **Update `updated` field** with the current date
- **Update `today.json`** daily (or create an n8n scheduled job)
- **Archive old crystals** - don't delete, move to `crystals/archive/`

---

## Copy-Paste Prompt for Claude

If you're in a new Claude conversation and need to crystalize a document, paste this:

---

### START COPY-PASTE BLOCK ###

```
I need you to convert a document into a Memory Crystal JSON file for my Hoggle AI assistant project.

A Memory Crystal is a structured JSON file with this format:

{
  "crystal_id": "kebab-case-name",
  "crystal_type": "knowledge",
  "version": 1,
  "created": "YYYY-MM-DD",
  "updated": "YYYY-MM-DD",
  "description": "One sentence description",
  "tags": ["keyword1", "keyword2"],
  "data": {
    // structured content from the document
  }
}

Rules:
1. Preserve EXACT values - standard codes, MP values, dates, names
2. Use arrays for lists (assignments, standards, achievements)
3. Use objects for grouped data (categories, sections)
4. Include ALL detail - every rubric line, every achievement, every standard code
5. No student PII
6. Tags should be specific nouns someone would use when asking about this topic
7. Keep descriptions complete but concise

Here is the document to crystalize:

[PASTE YOUR DOCUMENT CONTENT HERE]
```

### END COPY-PASTE BLOCK ###

---

*When in doubt, include more detail rather than less. The model can ignore extra info, but it can't invent missing data.*
