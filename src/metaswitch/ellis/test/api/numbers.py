#!/usr/bin/python

# @file numbers.py
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
NUMBER_ID2 = uuid.UUID('c9b15e68-5e8b-4bcf-9523-3eda4e123456')
NUMBER_ID2_HEX = 'c9b15e685e8b4bcf95233eda4e123456'
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
        # Finish has an important side-effect - it sets _finished to True.  If out mocked version doesn't do this, we see multiple calls to finish.
        def finish(*args):
            self.handler._finished = True
        self.handler.finish = MagicMock(side_effect=finish)

    @patch("metaswitch.ellis.data.numbers.get_numbers")
    def test_get_no_numbers(self, get_numbers):
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        get_numbers.return_value = []
        self.handler.get("foobar")
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.finish.assert_called_once_with( { "numbers": [] } )

    @patch("metaswitch.ellis.remote.homestead.get_associated_privates")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    @patch("metaswitch.ellis.data.numbers.get_numbers")
    def test_get_one_number(self, get_numbers,
                                  HTTPCallbackGroup,
                                  get_associated_privates):
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        get_numbers.return_value = [{"number": SIP_URI, "number_id": NUMBER_ID, "gab_listed": GAB_LISTED}]
        HTTPCallbackGroup.return_value = MagicMock()

        self.handler.get("foobar")
        # Assert that we kick off asynchronous GET at homestead
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        HTTPCallbackGroup.assert_called_once_with(self.handler._on_get_success,
                                                  self.handler._on_get_failure)

        get_associated_privates.assert_called_once_with(SIP_URI,
                                                        self.handler._request_group.callback())
        # Simulate success of all requests.
        response = MagicMock()
        response.body = '{"%s": ["hidden@sip.com"]}' % SIP_URI
        self.handler._on_get_success([response])

        self.handler.finish.assert_called_once_with(
            {
                "numbers": [
                     {"number_id": NUMBER_ID_HEX,
                      "number": "5555550123",
                      "sip_username": "5555550123",
                      "domain": "ngv.metaswitch.com",
                      "gab_listed": GAB_LISTED,
                      "formatted_number": "(555) 555-0123",
                      "sip_uri": SIP_URI,
                      "private_id": "hidden@sip.com", }
                 ]
            })

    def test_get_two_numbers(self):
        self.get_two_numbers(False)

    def test_get_two_numbers_shared(self):
        self.get_two_numbers(True)

    @patch("metaswitch.ellis.remote.homestead.get_associated_privates")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    @patch("metaswitch.ellis.data.numbers.get_numbers")
    def get_two_numbers(self, shared_private_id, get_numbers,
                                                 HTTPCallbackGroup,
                                                 get_associated_privates):
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        get_numbers.return_value = [{"number": "sip:4155551234@sip.com", "number_id": NUMBER_ID, "gab_listed": 0},
                                    {"number": "sip:4155555678@sip.com", "number_id": NUMBER_ID2, "gab_listed": 1}]
        HTTPCallbackGroup.return_value = MagicMock()

        self.handler.get("foobar")

        # Simulate success of all requests.
        response1 = MagicMock()
        response1.body = '{"sip:4155551234@sip.com": ["hidden1@sip.com"]}'
        response2 = MagicMock()
        if shared_private_id:
            response2.body = '{"sip:4155555678@sip.com": ["hidden1@sip.com"]}'
        else:
            response2.body = '{"sip:4155555678@sip.com": ["hidden2@sip.com"]}'
        self.handler._on_get_success([response1, response2])

        self.handler.finish.assert_called_once_with(
                {
                    "numbers": [
                        {
                            "number_id": NUMBER_ID_HEX,
                            "number": "4155551234",
                            "sip_username": "4155551234",
                            "domain": "sip.com",
                            "gab_listed": 0,
                            "formatted_number": "(415) 555-1234",
                            "sip_uri": "sip:4155551234@sip.com",
                            "private_id": "hidden1@sip.com",
                        },
                        {
                            "number_id": NUMBER_ID2_HEX,
                            "number": "4155555678",
                            "sip_username": "4155555678",
                            "domain": "sip.com",
                            "gab_listed": 1,
                            "formatted_number": "(415) 555-5678",
                            "sip_uri": "sip:4155555678@sip.com",
                            "private_id": (shared_private_id and "hidden1@sip.com" or "hidden2@sip.com"),
                        }
                    ]
                })

    def test_post_mainline(self):
        self.post_mainline(False, None)

    def test_post_pstn(self):
        self.post_mainline(True, None)

    def test_post_associate(self):
        self.post_mainline(False, PRIVATE_ID)

    def test_post_associate_pstn(self):
        self.post_mainline(True, PRIVATE_ID)

    @patch("metaswitch.common.ifcs.generate_ifcs")
    @patch("metaswitch.ellis.remote.homestead.post_associated_public")
    @patch("metaswitch.ellis.remote.homestead.put_password")
    @patch("metaswitch.ellis.remote.homestead.put_filter_criteria")
    @patch("metaswitch.ellis.remote.xdm.put_simservs")
    @patch("metaswitch.common.utils.generate_sip_password")
    @patch("metaswitch.common.utils.sip_public_id_to_private")
    @patch("metaswitch.ellis.data.numbers.allocate_number")
    @patch("metaswitch.ellis.data.numbers.get_number")
    def post_mainline(self, pstn, private_id, get_number,
                                              allocate_number,
                                              sip_pub_to_priv,
                                              gen_sip_pass,
                                              post_simservs,
                                              put_filter_criteria,
                                              put_password,
                                              post_associated_public,
                                              generate_ifcs):
        # Setup
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.request.arguments = {}
        if pstn:
            self.request.arguments["pstn"] = ["true"]
        else:
            self.request.arguments["pstn"] = ["false"]
        if private_id:
            self.request.arguments["private_id"] = [private_id]
        allocate_number.return_value = NUMBER_ID
        gen_sip_pass.return_value = "sip_pass"
        sip_pub_to_priv.return_value = "generated_private_id"
        get_number.return_value = SIP_URI
        generate_ifcs.return_value = "ifcs"

        # Test
        self.handler.post("foobar")

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        allocate_number.assert_called_once_with(self.db_sess, USER_ID, pstn)
        get_number.assert_called_once_with(self.db_sess, NUMBER_ID, USER_ID)
        if not private_id:
            # We don't generate a pw if we are just associating a pub/priv id
            gen_sip_pass.assert_called_once_with()
            sip_pub_to_priv.assert_called_once_with(SIP_URI)
            put_password.assert_called_once_with("generated_private_id", "sip_pass", ANY)
            post_associated_public.assert_called_once_with("generated_private_id", SIP_URI, ANY)
        else:
            # We don't generate a pw if we are just associating a pub/priv id
            post_associated_public.assert_called_once_with(PRIVATE_ID, SIP_URI, ANY)

        generate_ifcs.assert_called_once_with(settings.SIP_DIGEST_REALM)
        put_filter_criteria.assert_called_once_with(SIP_URI, "ifcs", ANY)
        post_simservs.assert_called_once_with(SIP_URI, ANY, ANY)

        # Simulate success of all requests.
        self.handler._on_post_success([Mock(), Mock(), Mock()])
        post_response = { "number_id": NUMBER_ID_HEX,
                          "number": "5555550123",
                          "sip_username": "5555550123",
                          "formatted_number": "(555) 555-0123",
                          "sip_uri": SIP_URI,
                          "pstn": pstn }
        if private_id:
            post_response["private_id"] = private_id
        else:
            post_response["sip_password"] = "sip_pass"
            post_response["private_id"] = "generated_private_id"
        self.handler.finish.assert_called_once_with(post_response)


class TestNumberHandler(BaseTest):
    def setUp(self):
        super(TestNumberHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.NumberHandler(self.app, self.request)

    @patch("metaswitch.ellis.api.numbers._remove_public_id")
    def test_delete_mainline(self, _remove_public_id):
        # Setup
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.check_number_ownership = Mock()
        self.handler.finish = MagicMock()

        # Test
        self.handler.delete("foobar", SIP_URI)

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with("foobar")
        self.handler.check_number_ownership.assert_called_once_with(SIP_URI, USER_ID)
        _remove_public_id.assert_called_once_with(self.db_sess,
                                                  SIP_URI,
                                                  self.handler._on_delete_success,
                                                  self.handler._on_delete_failure)

        # Simulate success of all requests.
        self.handler._on_delete_success([Mock(), Mock(), Mock()])

        self.handler.finish.assert_called_once_with({})

    def test_remove_public_id(self):
        self.remove_public_id(False)

    def test_remove_last_public_id(self):
        self.remove_public_id(True)

    @patch("metaswitch.ellis.api.numbers._delete_number")
    @patch("metaswitch.ellis.remote.homestead.get_associated_publics")
    @patch("metaswitch.ellis.remote.homestead.get_associated_privates")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def remove_public_id(self, last_public_id, HTTPCallbackGroup,
                                               get_associated_privates,
                                               get_associated_publics,
                                               _delete_number):
        # Setup
        HTTPCallbackGroup.return_value = MagicMock()
        on_success_handler = MagicMock()
        on_failure_handler = MagicMock()

        # Test
        numbers._remove_public_id(self.db_sess,
                                  SIP_URI,
                                  on_success_handler,
                                  on_failure_handler)

        # Asserts
        get_associated_privates.assert_called_once_with(SIP_URI, ANY)
        HTTPCallbackGroup.assert_called_once_with(ANY, on_failure_handler)

        # Extract inner function and can call it with response
        on_get_privates_success = HTTPCallbackGroup.call_args[0][0]
        response = MagicMock()
        response.body = '{"%s": ["%s"]}' % (SIP_URI, PRIVATE_ID)
        on_get_privates_success([response])

        # Response should have been paresed now and a new call invoked
        get_associated_publics.assert_called_once_with(PRIVATE_ID, ANY)
        on_get_publics_success = HTTPCallbackGroup.call_args[0][0]
        response = MagicMock()
        if last_public_id:
            response.body = '{"%s": ["%s"]}' % (PRIVATE_ID, SIP_URI)
        else:
            response.body = '{"%s": ["another@sip.com", "%s"]}' % (PRIVATE_ID, SIP_URI)
        on_get_publics_success([response])

        # Returned a single public id, so we expect to delete the digest
        _delete_number.assert_called_once_with(self.db_sess,
                                               SIP_URI,
                                               PRIVATE_ID,
                                               last_public_id,
                                               on_success_handler,
                                               on_failure_handler)

    def test_delete_number(self):
        self.delete_number(True)

    def test_disassociate_number(self):
        self.delete_number(False)

    @patch("metaswitch.ellis.remote.homestead.delete_associated_public")
    @patch("metaswitch.ellis.remote.homestead.delete_password")
    @patch("metaswitch.ellis.remote.homestead.delete_filter_criteria")
    @patch("metaswitch.ellis.remote.xdm.delete_simservs")
    @patch("metaswitch.ellis.data.numbers.remove_owner")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def delete_number(self, delete_digest, HTTPCallbackGroup,
                                           remove_owner,
                                           delete_simservs,
                                           delete_filter_criteria,
                                           delete_password,
                                           delete_associated_public):
        # Setup
        HTTPCallbackGroup.return_value = MagicMock()
        on_success_handler = MagicMock()
        on_failure_handler = MagicMock()

        # Test
        numbers._delete_number(self.db_sess,
                               SIP_URI,
                               PRIVATE_ID,
                               delete_digest,
                               on_success_handler,
                               on_failure_handler)

        # Asserts
        remove_owner.assert_called_once_with(self.db_sess, SIP_URI)
        HTTPCallbackGroup.assert_called_once_with(on_success_handler,
                                                  on_failure_handler)
        if delete_digest:
            delete_password.assert_called_once_with(PRIVATE_ID, SIP_URI, ANY)
        else:
            delete_associated_public.assert_called_once_with(PRIVATE_ID, SIP_URI, ANY)
        delete_filter_criteria.assert_called_once_with(SIP_URI, ANY)
        delete_simservs.assert_called_once_with(SIP_URI, ANY)

class TestSipPasswordHandler(BaseTest):
    """
    Unit tests of the SipPasswordHandler class.
    """
    def setUp(self):
        super(TestSipPasswordHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.SipPasswordHandler(self.app, self.request)

    @patch("metaswitch.ellis.remote.homestead.put_password")
    @patch("metaswitch.ellis.remote.homestead.get_associated_privates")
    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    @patch("metaswitch.common.utils.generate_sip_password")
    @patch("metaswitch.ellis.data.numbers.allocate_number")
    @patch("metaswitch.ellis.data.numbers.get_number")
    def test_post_mainline(self, get_number,
                                 allocate_number,
                                 gen_sip_pass,
                                 HTTPCallbackGroup,
                                 get_associated_privates,
                                 put_password):
        # Setup
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.check_number_ownership = Mock()
        gen_sip_pass.return_value = "sip_pass"
        HTTPCallbackGroup.return_value = MagicMock()
        self.handler.finish = MagicMock()

        # Test
        self.handler.post("foobar", SIP_URI)

        # Assert
        HTTPCallbackGroup.assert_called_once_with(self.handler.on_get_privates_success,
                                                  self.handler.on_get_privates_failure)
        get_associated_privates.assert_called_once_with(SIP_URI,
                                                        self.handler._request_group.callback())
        # Invoke callback for returned private IDs and assert password is created
        response = MagicMock()
        response.body = '{"%s": ["hidden@sip.com"]}' % SIP_URI
        self.handler.on_get_privates_success([response])
        put_password.assert_called_once_with("hidden@sip.com",
                                             "sip_pass",
                                             self.handler.on_password_response)
        # Invoke call for password PUT
        response = MagicMock()
        response.code = 200
        self.handler.on_password_response(response)
        self.handler.finish.assert_called_once_with({"sip_password": "sip_pass"})


class TestRemoteProxyHandler(BaseTest):
    """
    Unit tests of the RemoteProxyHandler class.
    """
    def setUp(self):
        super(TestRemoteProxyHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.RemoteProxyHandler(self.app, self.request)
        self.handler.remote_get = MagicMock()
        self.handler.remote_put = MagicMock()

    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_get_mainline(self, HTTPCallbackGroup):
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
        self.handler.remote_get.assert_called_once_with(SIP_URI, ANY)

        # Simulate success of xdm request.
        self.handler._on_get_success([MagicMock(body="<xml>sample</xml>")])
        self.handler.finish.assert_called_once_with("<xml>sample</xml>")

    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_get_error(self, HTTPCallbackGroup):
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
        self.handler.remote_get.assert_called_once_with(SIP_URI, ANY)

        # Simulate error of xdm request.
        self.handler._on_get_failure(Mock())
        self.handler.send_error.assert_called_once_with(httplib.BAD_GATEWAY, reason="Upstream request failed.")


    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_put_mainline(self, HTTPCallbackGroup):
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
        self.handler.remote_put.assert_called_once_with(SIP_URI, "<xml>new</xml>", ANY)

        # Simulate success of xdm request.
        self.handler._on_put_success(Mock())
        self.handler.finish.assert_called_once_with(None)

    @patch("metaswitch.ellis.api.numbers.HTTPCallbackGroup")
    def test_put_error(self, HTTPCallbackGroup):
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
        self.handler.remote_put.assert_called_once_with(SIP_URI, "<xml>new</xml>", ANY)

        # Simulate error of xdm request.
        self.handler._on_put_failure(Mock())
        self.handler.send_error.assert_called_once_with(httplib.BAD_GATEWAY, reason="Upstream request failed.")

class TestSimservsHandler(BaseTest):
    """
    Unit tests of the SimservsHandler class.
    """
    @patch("metaswitch.ellis.remote.xdm.put_simservs")
    @patch("metaswitch.ellis.remote.xdm.get_simservs")
    def test_setup(self, get_simservs, put_simservs):
        # The bulk of the functionality is tested by the TestRemoteProxyHandler class
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.SimservsHandler(self.app, self.request)
        self.assertEquals(self.handler.remote_get, get_simservs)
        self.assertEquals(self.handler.remote_put, put_simservs)
        self.assertEquals(self.handler.remote_name, "Homer (simservs)")

class TestIFCsHandler(BaseTest):
    """
    Unit tests of the IFCsHandler class.
    """
    @patch("metaswitch.ellis.remote.homestead.put_filter_criteria")
    @patch("metaswitch.ellis.remote.homestead.get_filter_criteria")
    def test_setup(self, get_filter_criteria, put_filter_criteria):
        # The bulk of the functionality is tested by the TestRemoteProxyHandler class
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = numbers.IFCsHandler(self.app, self.request)
        self.assertEquals(self.handler.remote_get, get_filter_criteria)
        self.assertEquals(self.handler.remote_get, get_filter_criteria)
        self.assertEquals(self.handler.remote_name, "Homestead (iFC)")

if __name__ == "__main__":
    unittest.main()


