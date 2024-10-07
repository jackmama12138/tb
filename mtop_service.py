import hashlib
import json
import re
import time
import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from aiohttp_socks import ProxyConnector
from urllib.parse import quote, urlparse, urlunparse
from logger import logger
import config
import ssl

class MtopService:
    def __init__(self, options):
        self.proxy_str = options.get('proxy_str')
        self.cookie = options.get('cookie')
        self.app_key = config.APP_KEY
        self.m_h5_tk = None
        self.base_cookie = None
        self.session = None
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def create_session(self):
        if not self.session:
            connector = ProxyConnector.from_url(self.proxy_str, ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def execute_full_request(self):
        try:
            await self.create_session()
            await self.get_m_h5_tk()
            token = await self.get_h5token()
            if not token:
                raise Exception("获取h5token失败")
            result = await self.subscribe_msg(token)
            print(result)
            return result
        except Exception as e:
            logger.error(f"执行完整请求失败: {str(e)}")
            return {"error": str(e)}
        finally:
            await self.close_session()

    async def get_m_h5_tk(self):
        if self.m_h5_tk and self.base_cookie:
            return {'m_h5_tk': self.m_h5_tk, 'base_cookie': self.base_cookie}

        url = 'https://h5api.m.taobao.com/h5/mtop.tmall.kangaroo.core.service.route.aldlampservicefixedresv2/1.0/?jsv=2.7.2&appKey=12574478&t=1727771714071&sign=6af747d682e724ade16df4a6fbfd2087&api=mtop.tmall.kangaroo.core.service.route.AldLampServiceFixedResV2&v=1.0&timeout=3000&dataType=jsonp&valueType=original&jsonpIncPrefix=tbpc&ttid=1@tbwang_mac_1.0.0#pc&type=originaljsonp&callback=mtopjsonptbpc1&data={}'

        async with self.session.get(url, timeout=ClientTimeout(total=5)) as response:
            if response.status != 200:
                raise Exception(f"获取m_h5_tk失败。状态码: {response.status}")

            self.m_h5_tk = response.cookies.get('_m_h5_tk')
            if not self.m_h5_tk:
                raise Exception("响应中未找到_m_h5_tk cookie")

            self.m_h5_tk = self.m_h5_tk.value.split('_')[0]
            base_cookie = '; '.join([f"{k}={v.value}" for k, v in response.cookies.items()])
            self.base_cookie = f"mtop_partitioned_detect=1; {base_cookie}"
            return {'m_h5_tk': self.m_h5_tk, 'base_cookie': self.base_cookie}

    @staticmethod
    def parse_response(response_text, api):
        try:
            match = re.search(r'mtopjsonp\d+\((.*)\)', response_text)
            if match:
                parsed_json = json.loads(match.group(1))
            else:
                parsed_json = json.loads(response_text)

            if api == 'mtop.taobao.dreamweb.anchor.h5token':
                if 'data' in parsed_json and 'result' in parsed_json['data']:
                    return parsed_json['data']['result']
                else:
                    raise Exception("h5token响应格式异常")
            elif api == 'mtop.taobao.powermsg.h5.msg.subscribe':
                return parsed_json
            else:
                raise Exception(f"未知的API: {api}")
        except json.JSONDecodeError:
            raise Exception("JSON解析失败")

    async def get_h5token(self):
        t = int(time.time() * 1000)
        options = {
            'time': t,
            'api': 'mtop.taobao.dreamweb.anchor.h5token',
            'api_version': '1.0',
            'data': {'appKey': "H5_25278248"}
        }
        return await self.send_request(options)

    async def subscribe_msg(self, token):
        t = int(time.time() * 1000)
        options = {
            'time': t,
            'api': 'mtop.taobao.powermsg.h5.msg.subscribe',
            'data': {
                'namespace': 1,
                'topic': 'd7250b19-bae8-4720-97d4-08e2b07d9130',
                'role': 3,
                'sdkVersion': "h5_3.4.2",
                'tag': "tb",
                'appKey': "H5_25278248",
                'utdId': "9450066120_455",
                'isSec': 0,
                'token': token,
                'timestamp': t,
                'ext': t
            },
            'api_version': '1.0',
        }
        return await self.send_request(options)

    @staticmethod
    def md5(string):
        return hashlib.md5(string.encode()).hexdigest()

    async def get_sign(self, m_h5_tk, data, time):
        return self.md5(f"{m_h5_tk}&{time}&{self.app_key}&{json.dumps(data)}")

    async def send_request(self, options):
        try:
            m_h5_tk_data = await self.get_m_h5_tk()
            m_h5_tk = m_h5_tk_data['m_h5_tk']
            base_cookie = m_h5_tk_data['base_cookie']
            sign = await self.get_sign(m_h5_tk, options['data'], options['time'])
            api, data, time, api_version = options['api'], options['data'], options['time'], options['api_version']

            url = f"https://h5api.m.taobao.com/h5/{api}/{api_version}/?jsv=2.7.2&appKey={self.app_key}&t={time}&sign={sign}&api={api}&v={api_version}&dataType=jsonp&callback=mtopjsonp1&data={quote(json.dumps(data))}"
            headers = {
                'accept': '*/*',
                'Host': 'h5api.m.taobao.com',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.1.0 Safari/537.36',
                'referer': 'https://main.m.taobao.com/',
                'Cookie': f"{base_cookie};{self.cookie}"
            }

            async with self.session.get(url, headers=headers, timeout=ClientTimeout(total=5)) as response:
                response_text = await response.text()
                return self.parse_response(response_text, api)
        except Exception as e:
            logger.error(f"发送请求时出错: {str(e)}")
            return {"error": str(e)}