import requests
import json


def get_proxy_ips(num_batches=3):
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
                    print("The API doesn't support providing service to your current IP address. Please try using a different IP.")
            except json.JSONDecodeError:
                pass  # If we can't parse the error as JSON, we'll just skip this part

    # Save all the formatted proxies to proxyPools.py
    with open('proxyPools.py', 'w') as f:
        f.write("proxyPool = [\n")
        for proxy in all_formatted_proxies:
            f.write(f"    '{proxy}',\n")
        f.write("]\n")
    
    print(f"Total of {len(all_formatted_proxies)} Proxy IPs have been successfully fetched and saved to proxyPools.py")

if __name__ == "__main__":
    get_proxy_ips()
