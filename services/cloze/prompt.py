PROMPT = """
You are generating Russian cloze tasks for language learners.

INPUT:
- target lemma: {lemma}
- target POS: {pos}

RULES:
1. Create ONE simple Russian sentence (5-10 words).
2. The sentence MUST include the target lemma naturally.

3. Choose ONE REAL word from the sentence (NOT the target lemma).
4. Replace that word with <...> using the EXACT original surface form.

❗ DO NOT write placeholders like <word>, <noun>, <something>.
❗ The text inside <> MUST be an actual word from the sentence.

Example:
"Это был бесконечный <день>."
NOT:
"Это был бесконечный <word>."

5. The blank word must:
   - be a content word (NOUN, VERB, ADJ)
   - be inferable from context

6. Generate 5 distractors:
   - same POS as the blank
   - grammatically valid
   - semantically wrong in context

7. Output JSON only.

FORMAT:
{{
  "sentence": "...",
  "distractors": ["...", "...", "...", "...", "..."]
}}
"""