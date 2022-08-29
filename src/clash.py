from __future__ import annotations

import subprocess
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep
from typing import List, Union, Dict

import requests
import yaml
from InquirerPy import inquirer

from .utils import find_free_port

BASE_PROFILE = {
    'allow-lan': False,
    'mode': 'global',
    'log-level': 'warning',
    'ipv6': True,
    'dns': {'enable': False},
    'proxies': []
}


def choose_profile() -> Path:
    profiles_dir = Path.home() / '.config' / 'clash' / 'profiles'
    if profiles_dir.is_dir():
        list_file = profiles_dir / 'list.yml'
        list_raw = yaml.safe_load(list_file.open('r', encoding='utf-8'))

        profiles = {
            profile['name']: profiles_dir / profile['time']
            for profile in list_raw['files']
        }
        profile_chosen = inquirer.select(
            message='Select a profile:',
            choices=list(profiles.keys())
        ).execute()
        return profiles[profile_chosen]

    raise FileNotFoundError('Profiles directory not found.\n'
                            'Currently, this script should be used '
                            'with Clash for Windows installed.')


class Clash:
    def __init__(self, profile: ClashProfile):
        executable_path = Clash.get_executable()

        self.proxy_port = profile.proxy_port
        self.control_port = profile.control_port
        self.process = subprocess.Popen(
            [str(executable_path), '-f', str(profile.path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        try:
            requests.get(self.build_control_url()).raise_for_status()
        except requests.RequestException:
            raise RuntimeError('Clash server not properly started.')

    def get_proxies(self):
        response = requests.get(self.build_control_url('proxies/GLOBAL'))
        proxies: List[str] = response.json()['all']
        for i in ['DIRECT', 'REJECT']:
            proxies.remove(i)
        return proxies

    def set_proxy(self, proxy: str, close_connections=True):
        requests.put(self.build_control_url('proxies/GLOBAL'), json={
            'name': proxy
        })

        if close_connections:
            requests.delete(self.build_control_url('connections'))

    def get_proxies_config(self) -> dict:
        return {
            'all': f'socks5://localhost:{self.proxy_port}'
        }

    def build_control_url(self, path: str = '/') -> str:
        url = f'http://localhost:{self.control_port}'
        if path[0] != '/':
            url += '/'
        url += path
        return url

    @staticmethod
    def get_executable() -> Path:
        lib_dir = Path(__file__).parent.parent / 'lib'
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


class ClashProfile:
    def __init__(self, profile_path: Path):
        self._profile = deepcopy(BASE_PROFILE)

        self.proxy_port = find_free_port()
        self._profile['mixed-port'] = self.proxy_port

        self.control_port = find_free_port()
        self._profile['external-controller'] = f'localhost:{self.control_port}'

        user_profile: dict = yaml.safe_load(profile_path.open('r', encoding='utf-8'))

        for proxy in user_profile.get('proxies', []):
            if proxy['port'] <= 1:
                # Not really a node
                continue

            self._profile['proxies'].append(proxy)

        file = NamedTemporaryFile('w', encoding='utf-8', suffix='.yml', delete=False)
        yaml.dump(self._profile, file, allow_unicode=True, sort_keys=False)
        self.path = Path(file.name)
        file.close()


class ClashPool:
    def __init__(self, user_profile_path: Path, max_count: int = 10):
        self.user_profile_path = user_profile_path
        self.pool: List[List[Union[Clash, bool]]] = []  # (instance, working)
        self.occupations: Dict[str, int] = {}
        self.max_count = max_count

    def create(self):
        profile = ClashProfile(self.user_profile_path)
        instance = Clash(profile)
        self.pool.append([instance, False])

    def get_proxies(self):
        instance_index = self.get_instance()
        self.pool[instance_index][1] = True
        result = self.pool[instance_index][0].get_proxies()
        self.pool[instance_index][1] = False
        return result

    def make_proxy(self, proxy: str):
        instance_index = self.get_instance()
        self.pool[instance_index][1] = True
        self.occupations[proxy] = instance_index
        self.pool[instance_index][0].set_proxy(proxy)
        return self.pool[instance_index][0].get_proxies_config()

    def release_proxy(self, proxy: str):
        # warning: don't forget to call this
        instance_index = self.occupations[proxy]
        self.pool[instance_index][1] = False

    def get_instance(self) -> int:
        while True:
            for index, (instance, working) in enumerate(self.pool):
                if not working:
                    return index

            if len(self.pool) < self.max_count:
                self.create()
                return len(self.pool) - 1

            sleep(0.5)
