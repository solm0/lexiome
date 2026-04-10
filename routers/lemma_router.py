from fastapi import APIRouter, HTTPException
import json
import os

from services.hint.cache import exists, load, save
from services.hint.llm_hint import generate_sentences
from services.hint.validator import validate
from services.singleflight import run_once

router = APIRouter()

# -------------------------
# preload
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")

with open(os.path.join(DATA_DIR, "lemmas.json"), encoding="utf-8") as f:
    LEMMAS = json.load(f)

with open(os.path.join(DATA_DIR, "lines.json"), encoding="utf-8") as f:
    LINES = json.load(f)

# line_id → line
line_map = {l["line_id"]: l for l in LINES}

# -------------------------
# helpers
# -------------------------

async def get_hints(lemma: str, pos: str):
    key = f"{lemma}_{pos}"

    if exists(key):
        return load(key)["content"]

    async def job():
        for _ in range(3):
            try:
                result = generate_sentences(lemma, pos)
                if validate(result, lemma):
                    save(key, result)
                    return result["content"]
            except Exception as e:
                print("RETRY ERROR:", e)
        raise HTTPException(status_code=500, detail="LLM failed")

    return await run_once(key, job)


def get_relationships(lemma_key: str):
    data = LEMMAS.get(lemma_key)
    if not data:
        return {"related_words": [], "antonyms": []}

    return {
        "related_words": data.get("related_words", []),
        "antonyms": data.get("antonyms", [])
    }


def get_kwic(lemma_key: str):
    data = LEMMAS.get(lemma_key)
    if not data:
        return []

    top_lines = data.get("top_lines", [])
    n = len(top_lines)

    if n == 0:
        return []

    k = min(10, n)

    result = []
    step = n / k

    for i in range(k):
        idx = int(i * step)
        lid = top_lines[idx]

        line = line_map.get(lid)
        if not line:
            continue

        result.append({
            "line_id": lid,
            "tokens": line["tokens"]
        })

    return result

# -------------------------
# API
# -------------------------

@router.get("/lemma")
async def get_lemma(lemma: str, pos: str):
    key = f"{lemma}_{pos}"

    relationships = get_relationships(key)
    kwic = get_kwic(key)
    hints = await get_hints(lemma, pos)

    return {
        "lemma": lemma,
        "pos": pos,
        "expansions": [
            {
                "type": "relationships",
                "content": relationships
            },
            {
                "type": "kwic",
                "content": kwic
            },
            {
                "type": "hints",
                "content": hints
            }
        ]
    }