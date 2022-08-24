from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml
from InquirerPy import inquirer

BASE_PROFILE = {
    'port': 57890,
    'socks-port': 57891,
    'allow-lan': False,
    'mode': 'global',
    'log-level': 'warning',
    'ipv6': True,
    'external-controller': f'localhost:57899',
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


def build_profile(profile_path: Path = choose_profile()) -> Path:
    profile = deepcopy(BASE_PROFILE)
    user_profile: dict = yaml.safe_load(profile_path.open('r', encoding='utf-8'))

    for proxy in user_profile.get('proxies', []):
        if proxy['port'] <= 1:
            # Not really a node
            continue

        profile['proxies'].append(proxy)

    file = NamedTemporaryFile('w', encoding='utf-8', suffix='.yml', delete=False)
    yaml.dump(profile, file, allow_unicode=True, sort_keys=False)
    file_path = Path(file.name)
    file.close()

    return file_path
