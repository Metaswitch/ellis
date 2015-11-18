#!/usr/bin/env python

# @file main.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.


import os
import argparse
import logging
import prctl
import signal
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

    # Fork off a child process per core.  In the parent process, the
    # fork_processes call blocks until the children exit.
    num_processes = settings.TORNADO_PROCESSES_PER_CORE * tornado.process.cpu_count()
    task_id = tornado.process.fork_processes(num_processes)
    if task_id is not None:
        prctl.prctl(prctl.NAME, "ellis")
        prctl.prctl(prctl.PDEATHSIG, signal.SIGTERM)
        logging_config.configure_logging(settings.LOG_LEVEL, settings.LOGS_DIR, settings.LOG_FILE_PREFIX, task_id)
        # We're a child process, start up.
        _log.info("Process %s starting up", task_id)
        connection.init_connection()

        http_server = httpserver.HTTPServer(application)
        unix_socket = bind_unix_socket(settings.HTTP_UNIX + "-" + str(task_id),
                                       0666);
        http_server.add_socket(unix_socket)

        homestead.ping()
        background.start_background_worker_io_loop()
        io_loop = tornado.ioloop.IOLoop.instance()
        io_loop.start()
    else:
        # This shouldn't happen since the children should run their IOLoops
        # forever.
        _log.critical("Children all exited")

if __name__ == '__main__':
    standalone()
