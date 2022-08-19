import subprocess
from pathlib import Path
from typing import List

import requests

from console import console
from profiles import CONTROLLER_PORT


class Clash:
    started = False

    def __init__(self, profile_path: Path):
        executable_path = Clash.get_executable()
        self.process = subprocess.Popen(
            [str(executable_path), '-f', str(profile_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        try:
            requests.get(f'http://localhost:{CONTROLLER_PORT}').raise_for_status()
        except requests.RequestException:
            raise RuntimeError('Clash server not properly started.')
        console.log('Clash server started.')
        self.started = True

    def get_proxies(self):
        response = requests.get(f'http://localhost:{CONTROLLER_PORT}/proxies/GLOBAL')
        proxies: List[str] = response.json()['all']
        for i in ['DIRECT', 'REJECT']:
            proxies.remove(i)
        return proxies

    def set_proxy(self, proxy: str, close_connections=True):
        requests.put(f'http://localhost:{CONTROLLER_PORT}/proxies/GLOBAL', json={
            'name': proxy
        })

        if close_connections:
            requests.delete(f'http://localhost:{CONTROLLER_PORT}/connections')

    def stop(self):
        if self.started:
            self.process.terminate()
            console.log('Clash server stopped.')
            self.process = None
            self.started = False

    def __del__(self):
        self.stop()

    @staticmethod
    def get_executable() -> Path:
        lib_dir = Path(__file__).parent / 'lib'
        for file in lib_dir.iterdir():
            if file.is_file() and file.name.startswith('clash'):
                exe_path = file.resolve()
                try:
                    process = subprocess.run([str(exe_path), '-v'],
                                             capture_output=True,
                                             text=True)
                    process.check_returncode()

                    return exe_path
                except (OSError, subprocess.CalledProcessError):
                    raise RuntimeError(f'{file.name} is not a valid executable.\n'
                                       'Please make sure that only the executable for the '
                                       'current platform is present in the `lib` directory.')

        raise FileNotFoundError('No clash executable found.')
