import random, asyncio
from .prompt import PROMPT
from .schema import ClozeItem
from .cache import load_cache, save_cache

MAX_CACHE = 10


async def generate_one(llm, lemma, pos):
    prompt = PROMPT.format(lemma=lemma, pos=pos)
    res = await llm(prompt)
    return ClozeItem.model_validate_json(res)


async def fill_cache(llm, lemma, pos):
    key = f"{lemma}_{pos}"
    cache = load_cache(key)

    if len(cache) >= MAX_CACHE:
        return

    try:
        item = await generate_one(llm, lemma, pos)
        cache.append(item.model_dump())
        save_cache(key, cache)
    except:
        pass


async def get_cloze_items(llm, lemma, pos):
    key = f"{lemma}_{pos}"
    cache = load_cache(key)

    # 최초
    if len(cache) == 0:
        new_items = [await generate_one(llm, lemma, pos) for _ in range(3)]
        cache.extend([i.model_dump() for i in new_items])
        save_cache(key, cache)

        asyncio.create_task(fill_cache(llm, lemma, pos))
        return new_items

    # 캐시 사용
    selected = random.sample(cache, k=min(3, len(cache)))

    # 백그라운드 채우기
    if len(cache) < MAX_CACHE:
        asyncio.create_task(fill_cache(llm, lemma, pos))

    return [ClozeItem(**x) for x in selected]