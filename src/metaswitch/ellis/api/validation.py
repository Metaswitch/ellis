# @file validation.py
#
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by post at
# Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK


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
            if expected_type == STRING and not isinstance(val, basestring):
                _log.debug("Validation of %s failed, %s should be a string", data, name)
                return False, "%s should be a string" % name
            if expected_type != STRING:
                return False, "Unknown field type %s for %s" % (expected_type, name)
            if expected_type == STRING and not re.match(regex, val):
                _log.debug("Validation of %s failed, %s should match %s", data, name, regex)
                return False, "%s should match '%s'" % (name, regex)
    return True, None
