import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
APP_KEY = os.getenv('APP_KEY')
TIMEOUT = int(os.getenv('TIMEOUT', 5000))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
CONCURRENCY_LIMIT = int(os.getenv('CONCURRENCY_LIMIT', 5))