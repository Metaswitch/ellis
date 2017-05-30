# @file validation.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


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
