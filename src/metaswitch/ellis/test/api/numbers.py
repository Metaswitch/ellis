#!/usr/bin/python

# @file numbers.py
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


import uuid
import unittest
import httplib
from mock import MagicMock, ANY, Mock, patch

from metaswitch.ellis import settings
from metaswitch.ellis.api import numbers
from metaswitch.common.ifcs import generate_ifcs
from metaswitch.ellis.test.api._base import BaseTest

USER_ID = uuid.UUID('90babc2a-d376-494d-a94a-2b1aca07130b')
USER_ID_HEX = '90babc2ad376494da94a2b1aca07130b'
NUMBER_ID = uuid.UUID('c9b15e68-5e8b-4bcf-9523-3eda4e677afd')
NUMBER_ID_HEX = 'c9b15e685e8b4bcf95233eda4e677afd'
SIP_URI = "sip:5555550123@ngv.metaswitch.com"
PRIVATE_ID = "5555550123@ngv.metaswitch.com"
GAB_LISTED = 1

class TestNumbersHandler(BaseTest):
    """
    Detailed, isolated unit tests of the CredentialsHandler class.
    """
    def setUp(self):
        super(TestNumbersHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.NumbersHandler(self.app, self.request)

    @patch("metaswitch.ellis.data.numbers.get_numbers")
    def test_get_mainline(self, get_numbers):
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.finish = MagicMock()
        get_numbers.return_value = [{"number": SIP_URI,
                                     "number_id": NUMBER_ID,
                                     "gab_listed": GAB_LISTED}]
        self.handler.get("foobar")
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.finish.assert_called_once_with(
            {
                "numbers": [
                     {"number_id": NUMBER_ID_HEX,
                      "number": "5555550123",
                      "sip_username": "5555550123",
                      "domain": "ngv.metaswitch.com",
                      "gab_listed": GAB_LISTED,
                      "formatted_number": "(555) 555-0123",
                      "sip_uri": SIP_URI, }
                 ]
            })


    @patch("metaswitch.common.ifcs.generate_ifcs")
    @patch("metaswitch.ellis.remote.homestead.post_password")
    @patch("metaswitch.ellis.remote.homestead.put_filter_criteria")
    @patch("metaswitch.ellis.remote.xdm.put_simservs")
    @patch("metaswitch.common.utils.generate_sip_password")
    @patch("metaswitch.ellis.data.numbers.allocate_number")
    @patch("metaswitch.ellis.data.numbers.get_number")
    def test_post_mainline(self, get_number,
                                 allocate_number,
                                 gen_sip_pass,
                                 post_simservs,
                                 put_filter_criteria,
                                 post_password,
                                 generate_ifcs):
        # Setup
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.finish = MagicMock()
        self.request.arguments = {"pstn": ['true']}
        allocate_number.return_value = NUMBER_ID
        gen_sip_pass.return_value = "sip_pass"
        get_number.return_value = SIP_URI
        generate_ifcs.return_value = "ifcs"

        # Test
        self.handler.post("foobar")

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        allocate_number.assert_called_once_with(self.db_sess, USER_ID, True)
        get_number.assert_called_once_with(self.db_sess, NUMBER_ID, USER_ID)
        gen_sip_pass.assert_called_once_with()
        post_password.assert_called_once_with(PRIVATE_ID, SIP_URI, "sip_pass", ANY)
        generate_ifcs.assert_called_once_with(settings.SIP_DIGEST_REALM)
        put_filter_criteria.assert_called_once_with(SIP_URI, "ifcs", ANY)
        post_simservs.assert_called_once_with(SIP_URI, ANY, ANY)

        # Simulate success of all requests.
        self.handler._on_post_success([Mock(), Mock(), Mock()])

        self.handler.finish.assert_called_once_with(
            {
                "number_id": NUMBER_ID_HEX,
                "number": "5555550123",
                "sip_username": "5555550123",
                "formatted_number": "(555) 555-0123",
                "sip_uri": SIP_URI,
                "sip_password": "sip_pass",
                "pstn": True
            })


class TestNumberHandler(BaseTest):
    def setUp(self):
        super(TestNumberHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.NumberHandler(self.app, self.request)

    @patch("metaswitch.ellis.remote.homestead.delete_password")
    @patch("metaswitch.ellis.remote.homestead.delete_filter_criteria")
    @patch("metaswitch.ellis.remote.xdm.delete_simservs")
    @patch("metaswitch.ellis.data.numbers.remove_owner")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_delete_mainline(self, HTTPCallbackGroup,
                                      remove_owner,
                                      delete_simservs,
                                      delete_filter_criteria,
                                      delete_password):
        # Setup
        HTTPCallbackGroup.return_value = MagicMock()
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.check_number_ownership = Mock()
        self.handler.finish = MagicMock()

        # Test
        self.handler.delete("foobar", SIP_URI)

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.check_number_ownership.assert_called_once_with(SIP_URI, USER_ID)
        remove_owner.assert_called_once_with(self.db_sess, SIP_URI)
        HTTPCallbackGroup.assert_called_once_with(self.handler._on_delete_success,
                                                  self.handler._on_delete_failure)
        delete_password.assert_called_once_with(PRIVATE_ID, SIP_URI, ANY)
        delete_filter_criteria.assert_called_once_with(SIP_URI, ANY)
        delete_simservs.assert_called_once_with(SIP_URI, ANY)

        # Simulate success of all requests.
        self.handler._on_delete_success([Mock(), Mock(), Mock()])

        self.handler.finish.assert_called_once_with({})


class TestSimservsHandler(BaseTest):
    """
    Unit tests of the SimservsHandler class.
    """
    def setUp(self):
        super(TestSimservsHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.SimservsHandler(self.app, self.request)

    @patch("metaswitch.ellis.remote.xdm.get_simservs")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_get_mainline(self, HTTPCallbackGroup, get_simservs):
        # Setup
        HTTPCallbackGroup.return_value = MagicMock()
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.check_number_ownership = Mock()
        self.handler.finish = MagicMock()

        # Test
        self.handler.get("foobar", SIP_URI)

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.check_number_ownership.assert_called_once_with(SIP_URI, USER_ID)
        get_simservs.assert_called_once_with(SIP_URI, ANY)

        # Simulate success of xdm request.
        self.handler._on_get_success([MagicMock(body="<xml>sample</xml>")])
        self.handler.finish.assert_called_once_with("<xml>sample</xml>")

    @patch("metaswitch.ellis.remote.xdm.get_simservs")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_get_error(self, HTTPCallbackGroup, get_simservs):
        # Setup
        HTTPCallbackGroup.return_value = MagicMock()
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.check_number_ownership = Mock()
        self.handler.send_error = MagicMock()

        # Test
        self.handler.get("foobar", SIP_URI)

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.check_number_ownership.assert_called_once_with(SIP_URI, USER_ID)
        get_simservs.assert_called_once_with(SIP_URI, ANY)

        # Simulate error of xdm request.
        self.handler._on_get_failure(Mock())
        self.handler.send_error.assert_called_once_with(httplib.BAD_GATEWAY, reason="Upstream request failed.")


    @patch("metaswitch.ellis.remote.xdm.put_simservs")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_put_mainline(self, HTTPCallbackGroup, put_simservs):
        # Setup
        HTTPCallbackGroup.return_value = MagicMock()
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.check_number_ownership = Mock()
        self.request.body = "<xml>new</xml>"
        self.handler.finish = MagicMock()

        # Test
        self.handler.put("foobar", SIP_URI)

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.check_number_ownership.assert_called_once_with(SIP_URI, USER_ID)
        put_simservs.assert_called_once_with(SIP_URI, "<xml>new</xml>", ANY)

        # Simulate success of xdm request.
        self.handler._on_put_success(Mock())
        self.handler.finish.assert_called_once_with(None)

    @patch("metaswitch.ellis.remote.xdm.put_simservs")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_put_error(self, HTTPCallbackGroup, put_simservs):
        # Setup
        HTTPCallbackGroup.return_value = MagicMock()
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.check_number_ownership = Mock()
        self.request.body = "<xml>new</xml>"
        self.handler.send_error = MagicMock()

        # Test
        self.handler.put("foobar", SIP_URI)

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.check_number_ownership.assert_called_once_with(SIP_URI, USER_ID)
        put_simservs.assert_called_once_with(SIP_URI, "<xml>new</xml>", ANY)

        # Simulate error of xdm request.
        self.handler._on_put_failure(Mock())
        self.handler.send_error.assert_called_once_with(httplib.BAD_GATEWAY, reason="Upstream request failed.")


if __name__ == "__main__":
    unittest.main()
