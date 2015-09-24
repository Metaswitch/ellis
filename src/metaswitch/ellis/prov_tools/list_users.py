#!/usr/share/clearwater/clearwater-prov-tools/env/bin/python

# @file list_users.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015  Metaswitch Networks Ltd
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

import sys
import logging
import argparse
import time

from tornado.web import HTTPError
from metaswitch.ellis import settings
from metaswitch.ellis.prov_tools import utils

_log = logging.getLogger();

def pace_wrapper(iterator, pace=10):
    next_time = time.time()
    for item in iterator:
        now_time = time.time()
        if now_time < next_time:
            time.sleep(next_time - now_time)
        else:
            next_time = now_time
        next_time += 1.0 / pace
        yield item

def main():
    parser = argparse.ArgumentParser(description="List users")
    parser.add_argument("-k", "--keep-going", action="store_true", dest="keep_going", help="keep going on errors")
    parser.add_argument("--hsprov", metavar="IP:PORT", action="store", help="IP address and port of homestead-prov")
    parser.add_argument("--full", action="store_true", help="displays full information for each user")
    parser.add_argument("--pace", action="store", help="sets the target number of users to list per second")
    parser.add_argument("-f", "--force", action="store_true", dest="force", help="forces specified pace")
    args = parser.parse_args()

    utils.setup_logging()
    settings.HOMESTEAD_URL = args.hsprov or settings.HOMESTEAD_URL
    default_pace = 5 if args.full else 500
    pace = int(args.pace) if args.pace else default_pace

    # Check the pace and get confirmation if it's too high
    if pace > default_pace and not args.force:
        if args.full:
            print("Pace %d greater than recommended value (%d) when --full specified" % (pace, default_pace))
        else:
            print("Pace %d greater than recommended value (%d)" % (pace, default_pace))
        print("This may impact call processing!  Are you sure?")
        print("Type <yes> below or rerun with --force to confirm")
        if raw_input().lower() == "yes":
            print("Continuing...")
        else:
            print("Aborting!")
            sys.exit(1)

    if not utils.check_connection():
        sys.exit(1)

    success = True
    try:
        for public_id in pace_wrapper(utils.list_users(keep_going=args.keep_going), pace=pace):
            if args.full:
                if not utils.display_user(public_id):
                    success = False
            else:
                print "%s" % (public_id,)
            sys.stdout.flush()

            if not success and not args.keep_going:
                break
    except HTTPError:
        success = False

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
