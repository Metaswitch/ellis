# @file _base.py
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

