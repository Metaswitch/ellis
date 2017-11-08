#!/usr/share/clearwater/clearwater-prov-tools/env/bin/python

# @file create_user.py
#
# Copyright (C) Metaswitch Networks 2016
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
    parser = argparse.ArgumentParser(description="Create user")
    parser.add_argument("-k", "--keep-going", action="store_true", dest="keep_going", help="keep going on errors")
    parser.add_argument("--hsprov", metavar="IP:PORT", action="store", help="IP address and port of homestead-prov")
    parser.add_argument("--plaintext", action="store_true", help="store password in plaintext")
    parser.add_argument("--ifc", metavar="iFC-FILE", action="store", dest="ifc_file", help="XML file containing the iFC")
    parser.add_argument("--prefix", action="store", default="123", dest="twin_prefix", help="twin-prefix (default: 123)")
    parser.add_argument("--impi", action="store", default="", dest="impi", help="IMPI (default: derived from the IMPU)")
    parser.add_argument("dns", metavar="<directory-number>[..<directory-number>]")
    parser.add_argument("domain", metavar="<domain>")
    parser.add_argument("password", metavar="<password>")
    args = parser.parse_args()

    utils.setup_logging()
    settings.HOMESTEAD_URL = args.hsprov or settings.HOMESTEAD_URL
    ifc = utils.build_ifc(args.ifc_file, args.domain, args.twin_prefix)
    if not ifc:
        sys.exit(1)

    if not utils.check_connection():
        sys.exit(1)

    # We use sys.stdout.write to print to stdout without a newline, so we can
    # indicate progress to the user
    sys.stdout.write("Creating users...")
    sys.stdout.flush()
    count = 0
    errors = 0
    for dn in utils.parse_dn_ranges(args.dns):
        success = True
        count += 1
        sys.stdout.write(".")
        sys.stdout.flush()
        public_id = "sip:%s@%s" % (dn, args.domain)
        private_id = "%s@%s" % (dn, args.domain)

        if args.impi != "":
            private_id = args.impi

        if utils.create_user(private_id, public_id, args.domain, args.password, ifc, plaintext=args.plaintext):
            if not utils.display_user(public_id, quiet=True):
                success = False
        else:
            success = False

        if not success:
            errors += 1
            utils.delete_user(public_id, private_id, force=True)
            print("Failed to create a subscriber - {}.".format(dn))

            if not args.keep_going:
                if dn != args.dns:
                    print("Failed to create any subscribers beyond {}".format(dn))

                break

        if count == 100:
            print("")
            print("Created up to user {}".format(dn))
            count = 0

    if errors == 0:
        if count == 1:
            print("Success. Subscriber {} has been created.".format(args.dns))
        else:
            print("Success. {} subscriber(s) have been created.".format(count))

        sys.exit(0)
    else:
        print("Finished, but failed to create all subscribers. See logs above for individual subscribers.")
        sys.exit(1)

if __name__ == '__main__':
    main()
