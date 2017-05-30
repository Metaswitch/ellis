# @file _base.py
#
# Copyright (C) Metaswitch Networks 2013
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import unittest
import re

from mock import MagicMock, Mock

from metaswitch.ellis.data import connection

class BaseDataTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.mock_session = Mock()
        self.mock_cursor = MagicMock()
        def execute(sql, params={}):
            for key in params.keys():
                self.assertTrue(re.search(r"(\A|\s|\n|\():%s\b" % key, sql),
                                "Parameter wasn't used: %s in %s" % (key, sql))
            for param in re.findall(r'\w+(?=:)', sql):
                self.assertTrue(param in params,
                                "SQL %s contained a parameter %s that wasn't present in %s" %
                                (sql, param, params))

            return self.mock_cursor
        self.mock_session.execute = Mock(side_effect=execute)
        self.mock_prep_query = MagicMock()
        self.mock_cursor.prepare_query = MagicMock(return_value=self.mock_prep_query)
        connection.Session = Mock(return_value=self.mock_session)

