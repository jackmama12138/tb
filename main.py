import asyncio
from mtop_service import MtopService
from logger import logger
from concurrency_queue import add_to_queue
import random
from cookies import cookies
from proxyPools import proxyPool
from utils import random_string
import json

MAX_CONCURRENT_TASKS = 1
current_cookie_index = 0


async def create_task():
    global current_cookie_index
    time = int(asyncio.get_event_loop().time() * 1000)
    options = {
        'proxy_str': random.choice(proxyPool),
        # 'cookie': cookies[current_cookie_index % len(cookies)]
        # 'proxy_str': '',
        'cookie': ''
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

    for index, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"任务 {index + 1} 失败: {str(result)}")
        else:
            try:
                # Parse the result if it's a string
                if isinstance(result, str):
                    result = json.loads(result)
                
                if isinstance(result, dict):
                    if result.get('ret') and 'SUCCESS::' in result['ret'][0]:
                        logger.info(f"任务 {index + 1} 成功: API={result.get('api', 'Unknown')}, ret={result['ret']}")
                    else:
                        logger.warning(f"任务 {index + 1} 可能失败: API={result.get('api', 'Unknown')}, ret={result.get('ret', 'Unknown')}")
                else:
                    logger.warning(f"任务 {index + 1} 返回了意外的结果类型: {type(result)}")
                    logger.warning(f"结果内容: {result}")
            except json.JSONDecodeError:
                logger.error(f"任务 {index + 1} 返回的结果无法解析为JSON: {result}")
            except Exception as e:
                logger.error(f"任务 {index + 1} 处理结果时发生错误: {str(e)}")

    logger.info(f"完成一批任务，共 {len(tasks)} 个任务")


async def main():
    logger.info('任务调度已启动')
    while True:
        await execute_batch()
        await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
