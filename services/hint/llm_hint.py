import json
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

MODEL = "gpt-5-mini"


def build_prompt(lemma: str, pos: str) -> str:
    pos_hint = {
        "VERB": "Describe actions or situations.",
        "NOUN": "Explain what it is or how it's used.",
        "ADJ": "Describe qualities.",
        "ADV": "Describe how or when something happens."
    }.get(pos, "Use simple explanation.")

    return f"""
You generate simple Russian sentences for language learners.

Target lemma: {lemma}
Part of speech: {pos}

Instructions:
- Use natural Russian.
- VERY IMPORTANT: very_easy sentences must be understandable by a 5-year-old.
- Include the lemma in each sentence at least once (any form).
- Wrap ALL occurrences of the lemma forms with < >.
- Produce exactly 6 sentences:
  - 2 very easy
  - 2 easy
  - 2 medium
- Keep sentences short.

Difficulty guide:
- very_easy: very short, present tense, no clauses, extremely simple words
- easy: simple sentences, maybe one clause
- medium: slightly longer, may include reason/condition

You may use patterns like:
- Когда ___, люди ___.
- ___ — это что-то, что ___.

But do NOT force patterns.

{pos_hint}

Output ONLY JSON:
{{
  "content": ["...", "...", "...", "...", "...", "..."]
}}
"""


def generate_sentences(lemma: str, pos: str) -> dict:
    prompt = build_prompt(lemma, pos)

    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )

        text = res.choices[0].message.content

        print("RAW LLM OUTPUT:")
        print(text)

        return json.loads(text)

    except Exception as e:
        print("LLM ERROR:", e)
        raise