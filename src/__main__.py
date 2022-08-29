from .clash import Clash
from .tester import Tester
from .profiles import build_profile


def start():
    profile_path = build_profile()
    clash_instance = Clash(profile_path)
    tester_instance = Tester(clash_instance)
    tester_instance()

    # cleanup
    clash_instance.stop()


start()
