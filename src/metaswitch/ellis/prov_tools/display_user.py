#!/usr/share/clearwater/clearwater-prov-tools/env/bin/python

# @file display_user.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import sys
import logging
import argparse
from metaswitch.ellis import settings
from metaswitch.ellis.prov_tools import utils

_log = logging.getLogger();

def main():
    parser = argparse.ArgumentParser(description="Display user")
    parser.add_argument("-k", "--keep-going", action="store_true", dest="keep_going", help="keep going on errors")
    parser.add_argument("-q", "--quiet", action="store_true", dest="quiet", help="suppress non-critical errors")
    parser.add_argument("-s", "--short", action="store_true", dest="short", help="less verbose display")
    parser.add_argument("--hsprov", metavar="IP:PORT", action="store", help="IP address and port of homestead-prov")
    parser.add_argument("dns", metavar="<directory-number>[..<directory-number>]")
    parser.add_argument("domain", metavar="<domain>")
    args = parser.parse_args()

    utils.setup_logging(level=logging.CRITICAL if args.quiet else logging.ERROR)
    settings.HOMESTEAD_URL = args.hsprov or settings.HOMESTEAD_URL

    if not utils.check_connection():
        sys.exit(1)

    success = True
    for dn in utils.parse_dn_ranges(args.dns):
        public_id = "sip:%s@%s" % (dn, args.domain)

        if not utils.display_user(public_id, short=args.short):
            success = False

        if not success and not args.keep_going:
            break

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
