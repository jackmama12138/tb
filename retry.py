import requests
from logger import logger
import config


def retry_request(request_config, retries=config.MAX_RETRIES):
    for i in range(retries):
        try:
            return requests.request(**request_config)
        except Exception as e:
            logger.error(f"请求失败, 重试第 {i + 1} 次: {str(e)}")
            if i == retries - 1:
                raise Exception('请求重试次数用尽')
