#!/usr/bin/python

# @file session.py
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

import unittest
import logging
from mock import MagicMock, patch

from metaswitch.ellis.api import session
from metaswitch.ellis.test.api._base import BaseTest

_log = logging.getLogger("ellis.api")

class TestSessionHandler(BaseTest):
    """
    Detailed, isolated unit tests of the SessionHandler class.
    """
    def setUp(self):
        super(TestSessionHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = session.SessionHandler(self.app, self.request)
        self.request.arguments = {}
        arguments = self.request.arguments
        def get_argument(name, default, *args):
            return arguments[name] if name in arguments else default
        self.handler.get_argument = MagicMock(side_effect=get_argument)
        self.request.headers = {}

    @patch("metaswitch.ellis.data.users.get_user_by_email_and_password", return_value = {})
    def test_post_mainline(self, get_user_by):
        # Setup
        self.request.arguments["email"] = "Clarkson"
        self.request.arguments["password"] = "squirrel"
        self.handler.set_status = MagicMock()
        self.handler.set_secure_cookie = MagicMock()
        self.handler.finish = MagicMock()
        get_user_by.return_value = {"user_id":         '123',
                                    "hashed_password": 'hashy',
                                    "full_name":       'Jeremy Clarkson',
                                    "email":           'clarkson@example.org',
                                    "expires":         0}

        # Test
        self.handler.post()

        # Asserts
        get_user_by.assert_called_once_with(self.db_sess, "Clarkson", "squirrel")
        self.handler.finish.assert_called_once_with({"username": "clarkson@example.org",
                                                     "full_name": "Jeremy Clarkson"})
        self.handler.set_secure_cookie.assert_called_once_with("username", "clarkson@example.org")

    @patch("metaswitch.ellis.data.users.get_user_by_email_and_password")
    def test_post_fail(self, get_user_by):
        # Setup
        self.request.arguments["email"] = "Clarkson"
        self.request.arguments["password"] = "squivvel"
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        def set_finished(*args):
            self.handler._finished = True
        self.handler.finish.side_effect = set_finished
        get_user_by.return_value = None

        # Test
        self.handler.post()

        # Asserts
        get_user_by.assert_called_once_with(self.db_sess, "Clarkson", "squivvel")
        self.handler.finish.assert_called_once_with({"status": 403, "detail": {}, "message": "Forbidden", "reason": "Incorrect username or password", "error": True})

if __name__ == "__main__":
    unittest.main()
