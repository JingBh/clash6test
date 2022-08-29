import asyncio

import nest_asyncio

from .clash import ClashPool, choose_profile
from .console import console, OutputQueue
from .tester import Tester

nest_asyncio.apply()


async def test_proxy(pool: ClashPool, proxy: str, output: OutputQueue):
    proxies_config = pool.make_proxy(proxy)
    tester = Tester(proxies_config)
    result = await asyncio.gather(
        asyncio.to_thread(tester.get_ip, 'ipv4'),
        asyncio.to_thread(tester.get_ip, 'ipv6')
    )
    output.add(proxy, *result)


async def start():
    console.log('Warning: This script does not work when system proxy is on.', style='yellow bold')

    user_profile = choose_profile()
    pool = ClashPool(user_profile)
    proxies = pool.get_proxies()
    output = OutputQueue(proxies)

    with output.live:
        tasks = set()

        for proxy in proxies:
            task = asyncio.create_task(test_proxy(pool, proxy, output))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
            await asyncio.sleep(0.5)

        await asyncio.wait(tasks)


asyncio.run(start())
