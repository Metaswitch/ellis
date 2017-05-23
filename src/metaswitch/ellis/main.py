#!/usr/bin/env python

# @file main.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import os
import argparse
import logging
import prctl
import tornado.web
import tornado.ioloop
import tornado.process
from tornado.netutil import bind_unix_socket
from metaswitch.ellis.api import URLS
from metaswitch.ellis.data import connection
from metaswitch.ellis import settings
from metaswitch.ellis.remote import homestead
from tornado import httpserver
from metaswitch.ellis import background
from metaswitch.common import utils, logging_config

_log = logging.getLogger("ellis")

def create_application():
    app_settings = {
        "gzip": True,
        "cookie_secret": settings.COOKIE_SECRET,
        "debug": settings.TORNADO_DEBUG,
    }
    application = tornado.web.Application(URLS, **app_settings)
    return application

def standalone():
    """
    Initializes Tornado and our application.  Forks worker processes to handle
    requests.  Does not return until all child processes exit normally.
    """

    # Parse arguments
    parser = argparse.ArgumentParser(description="Ellis web server")
    parser.add_argument("--background", action="store_true", help="Detach and run server in background")
    parser.add_argument("--log-level", default=2, type=int)
    args = parser.parse_args()

    prctl.prctl(prctl.NAME, "ellis")

    # We don't initialize logging until we fork because we want each child to
    # have its own logging and it's awkward to reconfigure logging that is
    # defined by the parent.
    application = create_application()

    if args.background:
        # Get a new logfile, rotating the old one if present.
        err_log_name = os.path.join(settings.LOGS_DIR, settings.LOG_FILE_PREFIX + "-err.log")
        try:
            os.rename(err_log_name, err_log_name + ".old")
        except OSError:
            pass
        # Fork into background.
        utils.daemonize(err_log_name)

    utils.install_sigusr1_handler(settings.LOG_FILE_PREFIX)

    # Drop a pidfile. We must keep a reference to the file object here, as this keeps
    # the file locked and provides extra protection against two processes running at
    # once.
    pidfile_lock = None
    try:
        pidfile_lock = utils.lock_and_write_pid_file(settings.PID_FILE) # noqa
    except IOError:
        # We failed to take the lock - another process is already running
        exit(1)

    # Only run one process, not one per core - we don't need the performance
    # and this keeps everything in one log file
    prctl.prctl(prctl.NAME, "ellis")
    logging_config.configure_logging(
            utils.map_clearwater_log_level(args.log_level),
            settings.LOGS_DIR,
            settings.LOG_FILE_PREFIX)
    _log.info("Ellis process starting up")
    connection.init_connection()

    http_server = httpserver.HTTPServer(application)
    unix_socket = bind_unix_socket(settings.HTTP_UNIX,
                                   0666);
    http_server.add_socket(unix_socket)

    homestead.ping()
    background.start_background_worker_io_loop()
    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.start()

if __name__ == '__main__':
    standalone()
