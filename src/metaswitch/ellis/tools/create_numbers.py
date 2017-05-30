#!/usr/bin/env python

# @file create_numbers.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import logging

from optparse import OptionParser

from metaswitch.ellis.data import numbers, connection
from sqlalchemy.exc import IntegrityError
from metaswitch.ellis import settings
from metaswitch.common import utils, logging_config

_log = logging.getLogger("ellis.create_numbers")

def standalone(start, num, pstn, realm):
    connection.init_connection()
    s = connection.Session()
    create_count = 0
    if not start:
        start = 5108580271 if pstn else 6505550000
    for x in xrange(num):
        if pstn:
            public_id = "sip:+1%d@%s" % (start + x, realm)
        else:
            public_id = "sip:%d@%s" % (start + x, realm)
        try:
            numbers.add_number_to_pool(s, public_id, pstn, False)
        except IntegrityError:
            # Entry already exists, not creating in db
            pass
        else:
            create_count += 1
    s.commit()
    print "Created %d numbers, %d already present in database" % (create_count, num - create_count)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-s",
                      "--start",
                      dest="start",
                      type="int",
                      help="Start creating with this number, defaulting to 5108580271 (PSTN) or 6505550000")
    parser.add_option("-c",
                      "--count",
                      dest="num",
                      type="int",
                      default=1,
                      help="Create this many numbers, if not specified, only one number will be created")
    parser.add_option("-p",
                      "--pstn",
                      action="store_true",
                      dest="pstn",
                      default=False,
                      help="If --pstn is specified, a PSTN-enabled number will be created")
    parser.add_option("-r",
                      "--realm",
                      dest="realm",
                      type="string",
                      default=settings.SIP_DIGEST_REALM,
                      help="Create numbers in this digest realm - if not specified, the home domain will be used")
    parser.add_option("--log-level",
                      dest="log_level",
                      default=2,
                      type="int")
    (options, args) = parser.parse_args()

    if args:
        parser.print_help()
    else:
        logging_config.configure_logging(
                utils.map_clearwater_log_level(options.log_level),
                settings.LOGS_DIR,
                settings.LOG_FILE_PREFIX,
                "create_db")

        standalone(options.start, options.num, options.pstn, options.realm)
