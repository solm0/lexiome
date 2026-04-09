from fastapi import APIRouter, HTTPException
from services.hint.cache import exists, load, save
from services.hint.llm_hint import generate_sentences
from services.hint.validator import validate
from services.singleflight import run_once

router = APIRouter()

@router.get("/hint")
async def get_hint(lemma: str, pos: str):
    key = f"{lemma}_{pos}"

    if exists(key):
        return load(key)

    async def job():
        for _ in range(3):
            try:
                result = generate_sentences(lemma, pos)
                if validate(result, lemma):
                    save(key, result)
                    return result
            except Exception as e:
                print("RETRY ERROR:", e)
        raise HTTPException(status_code=500, detail="LLM failed")

    return await run_once(key, job)