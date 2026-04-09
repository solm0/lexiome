from fastapi import APIRouter
from services.cloze.service import get_cloze_items
from services.singleflight import run_once
from openai import OpenAI
import os

router = APIRouter()


# LLM wrapper (기존 방식 그대로 유지)
async def llm(prompt: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI()

    res = await client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    print("RAW LLM:", res)

    # 안전 파싱
    try:
        return res.output_text
    except Exception:
        pass

    # fallback
    if res.output:
        for item in res.output:
            if item.content:
                for c in item.content:
                    if hasattr(c, "text") and c.text:
                        return c.text

    raise ValueError("LLM returned empty response")


@router.get("/cloze")
async def cloze(lemma: str, pos: str):
    key = f"cloze:{lemma}_{pos}"

    items = await run_once(
        key,
        lambda: get_cloze_items(llm, lemma, pos)
    )

    return [i.model_dump() for i in items]