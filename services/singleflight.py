import asyncio

locks = {}        # key -> asyncio.Lock
futures = {}      # key -> asyncio.Future


async def run_once(key: str, coro_fn):
    if key in futures:
        return await futures[key]

    lock = locks.setdefault(key, asyncio.Lock())

    async with lock:
        # double check
        if key in futures:
            return await futures[key]

        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        futures[key] = fut

        try:
            result = await coro_fn()
            fut.set_result(result)
            return result
        except Exception as e:
            fut.set_exception(e)
            raise
        finally:
            futures.pop(key, None)