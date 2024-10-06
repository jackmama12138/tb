import asyncio
from logger import logger
import config


class ConcurrencyQueue:
    def __init__(self, concurrency_limit=config.CONCURRENCY_LIMIT):
        self.concurrency_limit = concurrency_limit
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def add_to_queue(self, coro):
        async with self.semaphore:
            try:
                return await coro
            except Exception as e:
                logger.error(f"并发任务执行失败: {str(e)}")
                raise e

concurrency_queue = ConcurrencyQueue()


async def add_to_queue(coro):
    return await concurrency_queue.add_to_queue(coro)
