import requests
import json
import asyncio
import aiohttp
from mtop_service import MtopService


async def check_proxy(proxy):
    options = {'proxy_str': proxy, 'cookie': ''}  # 使用空cookie
    service = MtopService(options)
    try:
        await service.create_session()
        result = await service.get_m_h5_tk()
        return proxy if result else None
    except:
        return None
    finally:
        await service.close_session()


async def validate_proxies(proxies):
    tasks = [check_proxy(proxy) for proxy in proxies]
    results = await asyncio.gather(*tasks)
    return [proxy for proxy in results if proxy]


def get_proxy_ips(num_batches=4):  # 增加到4批，每批5个，总共20个
    url = "http://v2.api.juliangip.com/postpay/getips"
    params = {
        "auth_info": 1,
        "auto_white": 1,
        "num": 5,
        "pt": 1,
        "result_type": "text",
        "split": 1,
        "trade_no": "6534858850878215",
        "sign": "f29e2ef69b1deee5c2ec19b2338740f1"
    }

    all_formatted_proxies = []

    for _ in range(num_batches):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes

            # Split the response text into lines and remove any whitespace
            proxy_lines = [line.strip() for line in response.text.strip().split('\n')]

            # Format each proxy line
            for line in proxy_lines:
                ip, port, username, password = line.split(':')
                formatted_proxy = f'http://{username}:{password}@{ip}:{port}'
                all_formatted_proxies.append(formatted_proxy)

            print(f"Successfully fetched {len(proxy_lines)} proxy IPs")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching proxy IPs: {e}")

            # If there's an error, we'll check if it's the specific error message
            try:
                error_data = json.loads(response.text)
                if error_data.get('code') == 500 and "暂不支持向您添加的IP" in error_data.get('msg', ''):
                    print(
                        "The API doesn't support providing service to your current IP address. Please try using a different IP.")
            except json.JSONDecodeError:
                pass  # If we can't parse the error as JSON, we'll just skip this part

    # 在保存之前验证代理
    valid_proxies = asyncio.run(validate_proxies(all_formatted_proxies))

    # 保存有效的代理
    with open('proxyPools.py', 'w') as f:
        f.write("proxyPool = [\n")
        for proxy in valid_proxies:
            f.write(f"    '{proxy}',\n")
        f.write("]\n")

    print(f"Total of {len(valid_proxies)} valid Proxy IPs have been successfully saved to proxyPools.py")


if __name__ == "__main__":
    get_proxy_ips()
