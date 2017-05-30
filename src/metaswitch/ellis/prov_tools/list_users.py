#!/usr/share/clearwater/clearwater-prov-tools/env/bin/python

# @file list_users.py
#
# Copyright (C) Metaswitch Networks 2015
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

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
        now = time.time()
        if now < next_time:
            time.sleep(next_time - now)
        else:
            next_time = now
        next_time += 1.0 / pace
        yield item

def main():
    parser = argparse.ArgumentParser(description="List users")
    parser.add_argument("-k", "--keep-going", action="store_true", dest="keep_going", help="keep going on errors")
    parser.add_argument("--hsprov", metavar="IP:PORT", action="store", help="IP address and port of homestead-prov")
    parser.add_argument("--full", action="store_true", help="displays full information for each user")
    parser.add_argument("--pace", action="store", type=int, help="sets the target number of users to list per second")
    parser.add_argument("-f", "--force", action="store_true", dest="force", help="forces specified pace")
    args = parser.parse_args()

    utils.setup_logging()
    settings.HOMESTEAD_URL = args.hsprov or settings.HOMESTEAD_URL
    default_pace = 5 if args.full else 500
    pace = args.pace or default_pace

    # Check the pace and get confirmation if it's too high
    if pace > default_pace and not args.force:
        if args.full:
            print("Pace %d greater than recommended value (%d) when --full specified" % (pace, default_pace))
        else:
            print("Pace %d greater than recommended value (%d)" % (pace, default_pace))
        print("This may impact call processing!  Are you sure? [y/N]")
        print("(... or specify --force to skip this check and force the specified pace)")
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
