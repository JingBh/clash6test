from typing import List, Optional, Tuple

from rich.console import Console
from rich.live import Live
from rich.table import Table

from .utils import remove_emojis

console = Console()


class OutputQueue:
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.displayed: List[str] = []
        self.queue: List[Tuple[str, Optional[str], Optional[str]]] = []
        console.log(f'{len(proxies)} proxy nodes loaded.', style='green bold')

        # console.print('Test started, please wait...')
        # console.print('Name\tIPv4\tIPv6', style='bold')

        self.table = Table(title='Test Result')
        self.table.add_column('Name', justify='right', style='cyan', no_wrap=True)
        self.table.add_column('IPv4', no_wrap=True)
        self.table.add_column('IPv6', no_wrap=True)

        self.live = Live(self.table, auto_refresh=False, vertical_overflow='visible')

    def add(self, proxy: str, ipv4: Optional[str], ipv6: Optional[str]):
        self.queue.append((proxy, ipv4, ipv6))
        self.refresh()

    def refresh(self):
        for proxy in self.proxies:
            if proxy in self.displayed:
                continue

            for proxy_in_queue, ip4, ip6 in self.queue:
                if proxy == proxy_in_queue:
                    self.table.add_row(
                        remove_emojis(proxy),
                        '[red]✗ Timeout' if ip4 is None else f'[green]✓ {ip4}',
                        '[red]✗ Timeout' if ip6 is None else f'[green]✓ {ip6}'
                    )
                    self.live.refresh()
                    # console.print(
                    #     f'[cyan]{remove_emojis(proxy)}\t'
                    #     '[red]✗ Timeout' if ip4 is None else f'[green]✓ {ip4}\t'
                    #     '[red]✗ Timeout' if ip6 is None else f'[green]✓ {ip6}'
                    # )
                    self.displayed.append(proxy)
                    break
            else:
                break
