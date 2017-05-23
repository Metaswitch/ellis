# @file background.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import threading
import tornado

background_io_loop = None

def start_background_worker_io_loop():
    global background_io_loop
    if background_io_loop:
        return
    background_io_loop = tornado.ioloop.IOLoop()
    t = threading.Thread(name="bg_ioloop_thread", target=background_io_loop.start)
    t.daemon = True
    t.start()
