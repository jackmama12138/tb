import asyncio
from mtop_service import MtopService
from logger import logger
from concurrency_queue import add_to_queue
import random
from cookies import cookies
from proxyPools import proxyPool
from utils import random_string
import json

MAX_CONCURRENT_TASKS = 15
current_cookie_index = 0


async def create_task():
    global current_cookie_index
    time = int(asyncio.get_event_loop().time() * 1000)
    options = {
        'proxy_str': random.choice(proxyPool),
        'cookie': cookies[current_cookie_index % len(cookies)]
        # 'proxy_str': '',
        # 'cookie': ''
    }
    current_cookie_index += 1

    mtop_service = MtopService(options)

    request_options = {
        'time': time,
        'api': 'mtop.taobao.powermsg.h5.msg.subscribe',
        'data': {
            'namespace': 1,
            'topic': 'c756559a-d487-43fb-b3bf-4335dc8c0bca',
            'role': 3,
            'sdkVersion': "h5_3.4.2",
            'tag': "tb",
            'appKey': "H5_25278248",
            'utdId': "9450066120_450",
            'isSec': 0,
            'token': random_string(90),
            'timestamp': time,
            'ext': time
        },
        'api_version': '1.0',
    }

    return await mtop_service.send_request(request_options)


async def execute_batch():
    tasks = [create_task() for _ in range(MAX_CONCURRENT_TASKS)]
    results = await asyncio.gather(*[add_to_queue(task) for task in tasks], return_exceptions=True)

    successful_tasks = 0
    for index, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"任务 {index + 1} 失败: {str(result)}")
            continue
        try:
            if isinstance(result, str):
                result = json.loads(result)
            
            if isinstance(result, dict) and result.get('ret'):
                if 'SUCCESS::' in result['ret'][0]:
                    logger.info(f"任务 {index + 1} 成功: API={result.get('api', 'Unknown')}, ret={result['ret']}")
                    successful_tasks += 1
                else:
                    logger.error(f"任务 {index + 1} 失败: API={result.get('api', 'Unknown')}, ret={result['ret']}")
        except Exception as e:
            logger.error(f"任务 {index + 1} 处理结果时发生错误: {str(e)}")

    logger.info(f"完成一批任务，成功 {successful_tasks} 个任务，共 {len(tasks)} 个任务")


async def main():
    logger.info('任务调度已启动')
    while True:
        await execute_batch()
        await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
