import asyncio
from typing import Optional, Tuple

import requests

from .clash import Clash
from .console import OutputQueue
from .profiles import BASE_PROFILE


class Tester:

    def __init__(self, clash: Clash):
        self.clash = clash

    def __call__(self):
        proxies = self.clash.get_proxies()
        output = OutputQueue(proxies)

        with output.live:
            for proxy in proxies:
                self.clash.set_proxy(proxy)

                ip4, ip6 = asyncio.run(Tester.get_ip_all())
                output.add(proxy, ip4, ip6)

    @staticmethod
    async def get_ip_all() -> Tuple[Optional[str], Optional[str]]:
        return await asyncio.gather(
            Tester.get_ip('ipv4'),
            Tester.get_ip('ipv6')
        )

    @staticmethod
    async def get_ip(ip_type) -> Optional[str]:
        if ip_type != 'ipv4' and ip_type != 'ipv6':
            raise ValueError('`ip_type` should be either "ipv4" or "ipv6".')

        try:
            response = requests.get(f'https://api-{ip_type}.ip.sb/ip', headers={
                'User-Agent': 'Mozilla'  # otherwise it returns 403
            }, proxies={
                'all': f'socks5://localhost:{BASE_PROFILE["socks-port"]}'
            }, timeout=5)
        except requests.RequestException:
            return None

        return response.text.strip()
