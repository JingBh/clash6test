from typing import Optional

import requests


class Tester:

    def __init__(self, proxies_config):
        self.proxies_config = proxies_config

    def get_ip(self, ip_type) -> Optional[str]:
        if ip_type != 'ipv4' and ip_type != 'ipv6':
            raise ValueError('`ip_type` should be either "ipv4" or "ipv6".')

        try:
            response = requests.get(f'https://api-{ip_type}.ip.sb/ip', headers={
                'User-Agent': 'Mozilla'  # otherwise it returns 403
            }, proxies=self.proxies_config, timeout=5)
        except requests.RequestException:
            return None

        return response.text.strip()
