#!/usr/bin/python

# @file validation.py
#
# Copyright (C) Metaswitch Networks 2015
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import unittest

import metaswitch.ellis.api.validation as validation

class TestValidation(unittest.TestCase):

    def test_required(self):
        self.assertEquals(validation.validate({"foo": "bar"},
                                              {"foo": (validation.REQUIRED, validation.STRING, r'.*')}),
                          (True, None))
        self.assertEquals(validation.validate({"foo": "bar"},
                                              {"foo2": (validation.REQUIRED, validation.STRING, r'.*')}),
                          (False, 'Missing field: foo2'))


if __name__ == "__main__":
    unittest.main()
