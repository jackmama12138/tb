from logger import logger
import asyncio


async def batch_requests(tasks, batch_size, on_batch_complete=None):
    total_tasks = len(tasks)
    current_index = 0

    while current_index < total_tasks:
        batch_tasks = tasks[current_index:current_index + batch_size]

        try:
            await asyncio.gather(*[task() for task in batch_tasks])
            logger.info(f"成功完成了第 {current_index // batch_size + 1} 批次的任务")
            if on_batch_complete:
                on_batch_complete()
        except Exception as e:
            logger.error(f"第 {current_index // batch_size + 1} 批次任务执行失败: {str(e)}")

        current_index += batch_size
