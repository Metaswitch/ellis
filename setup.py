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
        "py-bcrypt==0.4",
        "tornado==2.3",
        "msgpack-python==0.4.6",
        "phonenumbers==7.1.1",
        "SQLAlchemy==1.0.9",
        "MySQL-python==1.2.5",
        "prctl==1.0.1",
        "pycurl==7.43.0"],
    tests_require=["pbr==1.6", "Mock"]
    )
