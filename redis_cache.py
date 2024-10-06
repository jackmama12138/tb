import json
import redis
from logger import logger
import config

redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)

class Cache:
    @staticmethod
    def get(key):
        try:
            value = redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis 获取错误: {str(e)}")
            return None

    @staticmethod
    def set(key, value, ttl=30):
        try:
            redis_client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.error(f"Redis 设置错误: {str(e)}")

cache = Cache()