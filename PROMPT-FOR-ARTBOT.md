# Prompt for ArtBot - Crystal/DSL Comparison

Copy and paste everything below the line into your ArtBot conversation.

---

## Context: A New Personality Configuration System

I've been designing a system called the **Personality DSL** (Domain-Specific Language) for my classroom AI assistant project (Hoggle). I want you to compare it to how YOUR personality and behavior is currently configured in the GAS stack, and help me figure out the best version for YOUR use case (a VTS warmup bot for non-technical teachers like Cat).

## What the Personality DSL Is

Instead of a wall of text in a system prompt, personality traits are stored as **structured JSON with defined scales**. Every trait has a current value AND a human-readable description of what that value means. The LLM reads both the value and the description, so behavior is consistent across interactions.

Here's an example:

```json
{
  "traits": {
    "warmth": {
      "current": 7,
      "scale": {
        "1": "Cold. Robotic. Answers only what is asked.",
        "3": "Friendly but reserved. Professional.",
        "5": "Genuinely kind. Encouraging.",
        "7": "Big sibling energy. Students feel safe asking questions.",
        "9": "Full emotional support. Reserved for struggling students.",
        "10": "Maximum warmth. Will hype someone up for getting ONE thing right."
      }
    },
    "push_to_look_deeper": {
      "current": 6,
      "scale": {
        "1": "Accepts surface-level observations. 'Good eye!' and moves on.",
        "3": "Gently asks one follow-up. 'What else do you notice?'",
        "5": "Asks 2-3 follow-ups. Guides toward composition, color, mood.",
        "7": "Socratic mode. Won't let them off easy. 'WHY do you think the artist chose that?'",
        "9": "Full art critic energy. Expects evidence for every claim.",
        "10": "Graduate seminar mode. Probably too much for middle school."
      }
    }
  }
}
```

The key insight: **numbers without definitions are meaningless** to a model. "warmth: 7" alone would be interpreted differently every time. But "warmth: 7 = Big sibling energy, students feel safe asking questions" is consistent.

This is called a DSL because it's essentially a custom mini-language: JSON is the container, English descriptions are the instructions, and the LLM is the interpreter.

## What I Need From You

1. **Compare this DSL approach to how your own personality/behavior is currently configured.** How are your VTS prompting behaviors, tone, and style currently defined? Is it a system prompt? Hardcoded logic? Something else?

2. **What would YOUR version of a personality crystal look like?** If we converted your current VTS bot behavior into this DSL format, what traits would matter? Think about:
   - How deeply you push students to observe
   - How warm vs. formal your tone is
   - How much art vocabulary you introduce
   - How you handle "I don't know" or silence
   - How you scaffold for different skill levels
   - How you adapt to different art pieces (abstract vs. representational, contemporary vs. classical)

3. **What's better about your current system that we should keep?** Maybe there are aspects of how you're configured now that are MORE flexible or useful than the DSL approach. I want to take the best of both.

4. **What's better about the DSL that your current system should adopt?** Maybe the defined scales, the tunability, the teacher-facing sliders would improve your system.

5. **Design a GUI concept for Cat.** Cat is a non-technical teacher. She needs:
   - A simple webapp (running on GAS deployment)
   - No raw JSON visible ever
   - Sliders and dropdowns that map to personality DSL values
   - Ability to pick an art piece, set guiding questions, adjust bot personality
   - Save/load different configurations for different lessons
   - Optimistic UI (saves to GAS CacheService fast, persists to Sheet in background)

6. **What VTS-specific traits would the DSL need?** Things Hoggle doesn't need but an art observation bot does:
   - Art vocabulary level
   - Cultural context sensitivity
   - How to handle controversial or challenging imagery
   - Observation vs. interpretation vs. evaluation progression
   - How to scaffold "I see / I think / I wonder" frameworks

Give me your honest comparison. What should we take from each approach to make the best possible version for teachers like Cat who want a customizable VTS warmup bot without touching code?
