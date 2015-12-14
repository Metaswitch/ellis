#!/usr/share/clearwater/clearwater-prov-tools/env/bin/python

# @file delete_user.py
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
from metaswitch.ellis import settings
from metaswitch.ellis.prov_tools import utils

_log = logging.getLogger();

def main():
    parser = argparse.ArgumentParser(description="Delete user")
    parser.add_argument("-f", "--force", action="store_true", dest="force", help="proceed with delete in the face of errors")
    parser.add_argument("-q", "--quiet", action="store_true", dest="quiet", help="silence 'forced' error messages")
    parser.add_argument("-y", "--yes", action="store_true", dest="no_prompt", help="auto-accept the prompt displayed before deleting the user(s)")
    parser.add_argument("--hsprov", metavar="IP:PORT", action="store", help="IP address and port of homestead-prov")
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

        if not utils.delete_user(private_id, public_id, force=args.force):
            success = False

        if not success and not args.force:
            break

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
