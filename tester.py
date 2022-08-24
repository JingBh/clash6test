import re
from typing import Optional

import requests
from rich.live import Live
from rich.table import Table

from console import console
from clash import Clash
from profiles import BASE_PROFILE


# Reference: https://stackoverflow.com/a/49986645/18176440
def remove_emojis(text: str) -> str:
    regrex_pattern = re.compile("["
                                "\U0001F600-\U0001F64F"  # emoticons
                                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                                "\U0001F680-\U0001F6FF"  # transport & map symbols
                                "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                "]+", flags=re.UNICODE)
    return regrex_pattern.sub(r'', text)


class Tester:

    def __init__(self, clash: Clash):
        self.clash = clash

    def __call__(self):
        proxies = self.clash.get_proxies()
        console.log(f'{len(proxies)} proxy nodes loaded.', style='green bold')

        table = Table(title='Test Result')
        table.add_column('Name', justify="right", style="cyan", no_wrap=True)
        table.add_column('IPv4', no_wrap=True)
        table.add_column('IPv6', no_wrap=True)

        live = Live(table, auto_refresh=False, vertical_overflow='visible')
        with live:
            for proxy in proxies:
                self.clash.set_proxy(proxy)
                ip4 = self.get_ip('ipv4')
                ip6 = self.get_ip('ipv6')

                table.add_row(
                    remove_emojis(proxy),
                    '[red]✗ Timeout' if ip4 is None else f'[green]✓ {ip4}',
                    '[red]✗ Timeout' if ip6 is None else f'[green]✓ {ip6}'
                )
                live.refresh()

    @staticmethod
    def get_ip(ip_type) -> Optional[str]:
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
