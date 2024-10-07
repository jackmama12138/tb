import asyncio
from mtop_service import MtopService
import time
from logger import logger
from cookies import cookies
from proxyPools import proxyPool
import random

MAX_CONCURRENT_TASKS = 5
current_cookie_index = 0

sem = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def create_task():
    global current_cookie_index
    if not proxyPool:
        return {"error": "没有可用的代理"}
    proxy_str = random.choice(proxyPool)
    options = {
        'proxy_str': proxy_str,
        'cookie': cookies[current_cookie_index % len(cookies)],
    }
    current_cookie_index = (current_cookie_index + 1) % len(cookies)
    mtop_service = MtopService(options)

    logger.info(f"使用代理: {proxy_str}")

    async with sem:
        try:
            result = await mtop_service.execute_full_request()
            return result
        except Exception as e:
            logger.error(f"任务失败，错误: {str(e)}")
            return {"error": str(e)}

async def execute_batch():
    tasks = [create_task() for _ in range(MAX_CONCURRENT_TASKS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful_tasks = 0
    for index, result in enumerate(results):
        if isinstance(result, dict):
            if "error" not in result:
                successful_tasks += 1
            else:
                logger.error(f"任务 {index + 1} 失败: {result['error']}")
        else:
            logger.error(f"任务 {index + 1} 失败: 未知错误")

    logger.info(f"完成一批任务，成功 {successful_tasks} 个任务，共 {len(tasks)} 个任务")

    # 保存当前 cookie 索引
    with open('cookie_index.txt', 'w') as f:
        f.write(str(current_cookie_index))

async def main():
    global current_cookie_index

    # 读取上次保存的 cookie 索引
    try:
        with open('cookie_index.txt', 'r') as f:
            content = f.read().strip()
            current_cookie_index = int(content) if content else 0
    except (FileNotFoundError, ValueError):
        current_cookie_index = 0

    # 确保 current_cookie_index 在有效范围内
    current_cookie_index = current_cookie_index % len(cookies)

    logger.info('任务调度已启动')
    while True:
        start_time = time.time()
        await execute_batch()
        elapsed_time = time.time() - start_time
        if elapsed_time < 5:
            await asyncio.sleep(5 - elapsed_time)

if __name__ == '__main__':
    asyncio.run(main())