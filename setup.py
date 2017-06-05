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
        "backports_abc==0.5",
        "backports.ssl_match_hostname==3.5.0.1",
        "certifi==2017.4.17",
        "msgpack-python==0.4.6",
        "MySQL-python==1.2.5",
        "phonenumbers==7.1.1",
        "prctl==1.0.1",
        "pycurl==7.43.0",
        "singledispatch==3.4.0.3",
        "six==1.10.0",
        "SQLAlchemy==1.0.9",
        "tornado==2.3"],
    tests_require=[
        "funcsigs==1.0.2",
        "Mock==2.0.0",
        "pbr==1.6",
        "six==1.10.0"]
    )
