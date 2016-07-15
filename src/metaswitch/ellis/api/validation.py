# @file validation.py
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
import re

_log = logging.getLogger("ellis.api")

STRING = "string"
REQUIRED = "required"
OPTIONAL = "optional"

def validate(data, patterns):
    for name, rule in patterns.iteritems():
        required, expected_type, regex = rule
        try:
            val = data[name]
        except KeyError:
            if required == REQUIRED:
                _log.debug("Validation of %s failed, missing field %s", data, name)
                return False, "Missing field: %s" % name
        else:
            if expected_type == STRING and not isinstance(val, basestring): # pragma: no cover
                _log.debug("Validation of %s failed, %s should be a string", data, name)
                return False, "%s should be a string" % name
            if expected_type != STRING: # pragma: no cover
                return False, "Unknown field type %s for %s" % (expected_type, name)
            if expected_type == STRING and not re.match(regex, val): # pragma: no cover
                _log.debug("Validation of %s failed, %s should match %s", data, name, regex)
                return False, "%s should match '%s'" % (name, regex)
    return True, None
