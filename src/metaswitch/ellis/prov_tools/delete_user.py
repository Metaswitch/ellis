#!/usr/share/clearwater/clearwater-prov-tools/env/bin/python

# @file delete_user.py
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
from metaswitch.ellis import settings
from metaswitch.ellis.prov_tools import utils

_log = logging.getLogger();

def main():
    parser = argparse.ArgumentParser(description="Delete user")
    parser.add_argument("-f", "--force", action="store_true", dest="force", help="proceed with delete in the face of errors")
    parser.add_argument("-q", "--quiet", action="store_true", dest="quiet", help="silence 'forced' error messages")
    parser.add_argument("-y", "--yes", action="store_true", dest="no_prompt", help="auto-accept the prompt displayed before deleting the user(s)")
    parser.add_argument("--hsprov", metavar="IP:PORT", action="store", help="IP address and port of homestead-prov")
    parser.add_argument("--impi", action="store", default="", dest="impi", help="IMPI (default: derived from the IMPU)")
    parser.add_argument("dns", metavar="<directory-number>[..<directory-number>]")
    parser.add_argument("domain", metavar="<domain>")
    args = parser.parse_args()

    utils.setup_logging(level=logging.CRITICAL if args.quiet else logging.ERROR)
    settings.HOMESTEAD_URL = args.hsprov or settings.HOMESTEAD_URL

    if not utils.check_connection():
        sys.exit(1)

    if not args.no_prompt:
        print 'Are you sure you wish to delete the following users: {}? [y/n]'.format(args.dns)
        choice = raw_input().lower()

        if choice != 'y':
            if choice != 'n':
                print "Exiting due to invalid input: Expected 'y' or 'n'."
            else:
                print "Exiting on user request."
            exit(0)

    success = True
    for dn in utils.parse_dn_ranges(args.dns):
        public_id = "sip:%s@%s" % (dn, args.domain)
        private_id = "%s@%s" % (dn, args.domain)

        if args.impi != "":
            private_id = args.impi

        if not utils.delete_user(private_id, public_id, force=args.force):
            success = False

        if not success and not args.force:
            break

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
