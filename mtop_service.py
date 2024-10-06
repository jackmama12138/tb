import hashlib
import json
import re
import requests
from requests.exceptions import RequestException
from urllib.parse import quote

from logger import logger
from validation import validate_params
import config


class MtopService:
    def __init__(self, options):
        self.proxy_str = options.get('proxy_str')
        self.cookie = options.get('cookie')
        self.app_key = config.APP_KEY
        self.m_h5_tk = None
        self.base_cookie = None

    async def get_m_h5_tk(self):
        if self.m_h5_tk and self.base_cookie:
            return {'m_h5_tk': self.m_h5_tk, 'base_cookie': self.base_cookie}

        try:
            request_config = {
                'url': 'https://h5api.m.taobao.com/h5/mtop.tmall.kangaroo.core.service.route.aldlampservicefixedresv2/1.0/?jsv=2.7.2&appKey=12574478&t=1727771714071&sign=6af747d682e724ade16df4a6fbfd2087&api=mtop.tmall.kangaroo.core.service.route.AldLampServiceFixedResV2&v=1.0&timeout=3000&dataType=jsonp&valueType=original&jsonpIncPrefix=tbpc&ttid=1@tbwang_mac_1.0.0#pc&type=originaljsonp&callback=mtopjsonptbpc1&data={}',
                'timeout': 2
            }

            if self.proxy_str:
                request_config['proxies'] = {'http': self.proxy_str, 'https': self.proxy_str}

            response = requests.get(**request_config)
            self.m_h5_tk = response.cookies['_m_h5_tk'].split('_')[0]
            base_cookie = '; '.join([f"{k}={v}" for k, v in response.cookies.items()])
            self.base_cookie = f"mtop_partitioned_detect=1; {base_cookie}"
            return {'m_h5_tk': self.m_h5_tk, 'base_cookie': self.base_cookie}
        except Exception as e:
            logger.error(f"获取_m_h5_tk失败: {str(e)}")
            raise Exception('获取_m_h5_tk失败')

    @staticmethod
    def md5(string):
        return hashlib.md5(string.encode()).hexdigest()

    async def get_sign(self, m_h5_tk, data, time):
        return self.md5(f"{m_h5_tk}&{time}&{self.app_key}&{json.dumps(data)}")

    async def send_request(self, options):
        validate_params(options, ['api', 'data', 'time'])

        m_h5_tk_data = await self.get_m_h5_tk()
        m_h5_tk = m_h5_tk_data['m_h5_tk']
        base_cookie = m_h5_tk_data['base_cookie']
        sign = await self.get_sign(m_h5_tk, options['data'], options['time'])
        api, data, time, api_version = options['api'], options['data'], options['time'], options['api_version']

        request_config = {
            'method': 'GET',
            'url': f"https://h5api.m.taobao.com/h5/{api}/{api_version}/?jsv=2.7.2&appKey={self.app_key}&t={time}&sign={sign}&api={api}&v={api_version}&dataType=jsonp&callback=mtopjsonp1&data={quote(json.dumps(data))}",
            'headers': {
                'accept': '*/*',
                'Host': 'h5api.m.taobao.com',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.1.0 Safari/537.36',
                'referer': 'https://main.m.taobao.com/',
                'Cookie': f"{base_cookie};{self.cookie}"
            },
            'timeout': 2
        }

        if self.proxy_str:
            request_config['proxies'] = {'http': self.proxy_str, 'https': self.proxy_str}

        try:
            response = requests.request(**request_config)
            result = self.parse_response(response.text)
            
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    result = {"raw_response": result}

            return result
        except RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def parse_response(response_text):
        if isinstance(response_text, str):
            match = re.search(r'mtopjsonp1\((.*)\)', response_text)
            if match:
                return json.loads(match.group(1))
            else:
                return response_text
        else:
            return response_text