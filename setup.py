# @file setup.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import logging
import sys

from setuptools import setup, find_packages
from logging import StreamHandler

_log = logging.getLogger("ellis")
_log.setLevel(logging.DEBUG)
_handler = StreamHandler(sys.stderr)
_handler.setLevel(logging.DEBUG)
_log.addHandler(_handler)

setup(
    name='ellis',
    version='0.1',
    packages=find_packages('src'),
    package_dir={'':'src'},
    package_data={
        '': ['*.eml'],
        },
    test_suite='metaswitch.ellis.test',
    install_requires=[
        "backports_abc",
        "backports.ssl_match_hostname",
        "certifi",
        "metaswitchcommon",
        "msgpack-python",
        "MySQL-python",
        "phonenumbers",
        "prctl",
        "pycurl",
        "py-bcrypt",
        "singledispatch",
        "six",
        "SQLAlchemy",
        "tornado",
        "defusedxml"
        ],
    tests_require=[
        "funcsigs",
        "Mock",
        "pbr",
        "six"]
    )
