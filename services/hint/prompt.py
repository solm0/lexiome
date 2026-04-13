def build_hint_prompt(lemma: str, pos: str) -> str:
    pos_hint = {
        "VERB": "Focus on actions people do. Describe situations where this action happens.",
        "NOUN": "Refer to it indirectly. Describe what people do with it or when they need it.",
        "ADJ": "Describe how something feels or appears when this quality is present.",
        "ADV": "Describe when or how actions happen in real situations."
    }.get(pos, "Use indirect hints.")

    return f"""
You generate Russian hint sentences for a guessing game.

Target word: {lemma}
Part of speech: {pos}

Goal:
- The reader should guess the word from the hints.
- Do NOT directly explain or define the word.

CRITICAL RULES:
- Do NOT use the target word or its forms.
- Refer to it indirectly (use "он", "она", "они", "это", etc.).
- Focus on situations, functions, and experiences.
- Sentences should feel like clues, not explanations.
- Avoid dictionary-style definitions.

Style:
- Use "ты", "мы", or general human experience.
- Natural, everyday situations.
- Slightly repetitive clues are OK.

Difficulty:
- 2 very easy
- 2 easy
- 2 medium
- Sentences can be longer than before.

Examples (for understanding style):
- Ты используешь это каждый день.
- Без этого ты не можешь хорошо видеть.
- Иногда они устают, если долго смотришь в экран.

Output ONLY JSON:
{{
  "content": ["...", "...", "...", "...", "...", "..."]
}}
"""