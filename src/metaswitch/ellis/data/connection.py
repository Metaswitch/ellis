# @file connection.py
#
# Copyright (C) Metaswitch Networks 2014
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import logging
from metaswitch.ellis import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_log = logging.getLogger("ellis.data")

engine = None
Session = None

def init_connection():
    global engine, Session
    engine = create_engine('mysql://%s:%s@%s:%s/%s?charset=utf8' % (
                               settings.SQL_USER,
                               settings.SQL_PW,
                               settings.SQL_HOST,
                               settings.SQL_PORT,
                               settings.SQL_DB,
                           ),
                           # Increase the allowed number of simultaneous
                           # database connections
                           pool_size=20,
                           # Avoid MySQL's 8hr idle timeout.
                           pool_recycle=3600)
    Session = sessionmaker(bind=engine)
