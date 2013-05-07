#!/usr/bin/env python

# @file create_numbers.py
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


import logging
import sys
import random

from optparse import OptionParser

from metaswitch.ellis import logging_config
from metaswitch.ellis.data import numbers, connection
from sqlalchemy.exc import IntegrityError
from metaswitch.ellis import settings

_log = logging.getLogger("ellis.create_numbers")

def standalone(start, num, pstn):
    connection.init_connection()
    s = connection.Session()
    create_count = 0
    if not start:
        start = 5108580271 if pstn else 6505550000
    for x in xrange(num):
        if pstn:
            public_id = "sip:+1%010d@%s" % (start + x, settings.SIP_DIGEST_REALM)
        else:
            public_id = "sip:%010d@%s" % (start + x, settings.SIP_DIGEST_REALM)
        try:
	    numbers.add_number_to_pool(s, public_id, pstn)
        except IntegrityError:
            # Entry already exists, not creating in db
	    pass
        else:
            create_count += 1	
    s.commit()
    print "Created %d numbers, %d already present in database" % (create_count, num - create_count)

if __name__ == '__main__':
    logging_config.configure_logging("create_db")
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
    (options, args) = parser.parse_args()
    if args:
      parser.print_help()
    else:
      standalone(options.start, options.num, options.pstn)
