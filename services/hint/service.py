import json
from openai import OpenAI
import os
from .prompt import build_hint_prompt

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

MODEL = "gpt-5-mini"

def generate_sentences(lemma: str, pos: str) -> dict:
    prompt = build_hint_prompt(lemma, pos)

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