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
import atexit
import tornado.web
import tornado.ioloop
import tornado.process
from tornado.netutil import bind_sockets
from metaswitch.ellis.api import URLS
from metaswitch.ellis.data import connection
from metaswitch.ellis import settings, logging_config
from metaswitch.ellis.remote import homestead
from tornado import httpserver
from metaswitch.ellis import background
from metaswitch.common import utils

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

    # We don't initialize logging until we fork because we want each child to
    # have its own logging and it's awkward to reconfigure logging that is
    # defined by the parent.
    application = create_application()
    listening_on_some_port = False

    http_sockets = None
    https_sockets = None

    if settings.ALLOW_HTTP:
        http_sockets = bind_sockets(settings.HTTP_PORT)
        listening_on_some_port = True

    if (os.path.exists(settings.TLS_CERTIFICATE) and
        os.path.exists(settings.TLS_PRIVATE_KEY)):
        https_sockets = bind_sockets(settings.HTTPS_PORT)
        listening_on_some_port = True

    if not listening_on_some_port:
        # We usually don't configure logging until after we fork but since
        # we're about to crash...
        logging_config.configure_logging("parent")
        _log.critical("Failed to listen on any ports.")
        raise Exception("Failed to listen on any ports")

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

    # Drop a pidfile.
    pid = os.getpid()
    with open(settings.PID_FILE, "w") as pidfile:
        pidfile.write(str(pid) + "\n")

    # Fork off a child process per core.  In the parent process, the
    # fork_processes call blocks until the children exit.
    num_processes = settings.TORNADO_PROCESSES_PER_CORE * tornado.process.cpu_count()
    task_id = tornado.process.fork_processes(num_processes)
    if task_id is not None:
        logging_config.configure_logging(task_id)
        # We're a child process, start up.
        _log.info("Process %s starting up", task_id)
        connection.init_connection()
        if http_sockets:
            _log.info("Going to listen for HTTP on port %s", settings.HTTP_PORT)
            http_server = httpserver.HTTPServer(application)
            http_server.add_sockets(http_sockets)
        else:
            _log.info("Not starting HTTP, set ALLOW_HTTP in local_settings.py to enable HTTP.")
        if https_sockets:
            _log.info("Going to listen for HTTPS on port %s", settings.HTTPS_PORT)
            https_server = httpserver.HTTPServer(application,
                       ssl_options={
                           "certfile": settings.TLS_CERTIFICATE,
                           "keyfile": settings.TLS_PRIVATE_KEY,
                       })
            https_server.add_sockets(https_sockets)
        else:
            _log.critical("Not starting HTTPS")
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
