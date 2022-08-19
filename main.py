#!/usr/bin/env python

"""
clash6test

A script to test whether your proxy nodes support IPv6.
"""

from clash import Clash
from profiles import build_profile
from tester import Tester

if __name__ == '__main__':
    profile_path = build_profile()
    clash = Clash(profile_path)
    tester = Tester(clash)
    tester()

    # cleanup
    clash.stop()
