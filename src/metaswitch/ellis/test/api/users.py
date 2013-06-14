#!/usr/bin/python

# @file users.py
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
import copy
from mock import MagicMock, ANY, Mock, patch

from tornado.web import HTTPError

from metaswitch.ellis import settings
from metaswitch.ellis.api import users
from metaswitch.ellis.api._base import HTTPErrorEx
from metaswitch.ellis.data import AlreadyExists
from metaswitch.ellis.data._base import NotFound
from metaswitch.ellis import settings
from metaswitch.ellis.test.api._base import BaseTest

EMAIL = "alice@example.com"
BAD_EMAIL = "nonuser@example.com"
PASSWORD = u"p\u00C3sswo"
FULL_NAME = "Alice"
USER_ID = uuid.UUID('90babc2a-d376-494d-a94a-2b1aca07130b')
DEFAULT_ARGUMENTS = { "password": PASSWORD,
                      "full_name": FULL_NAME,
                      "email": EMAIL }
TOKEN = "TestToken125"
NUMBER_ID = uuid.UUID('c9b15e68-5e8b-4bcf-9523-3eda4e677afd')
SIP_URI = "sip:5555550123@ngv.metaswitch.com"
PRIVATE_ID = "5555550123@ngv.metaswitch.com"
GAB_LISTED = 1
NUMBER_OBJ = { "number_id": NUMBER_ID,
               "number": SIP_URI,
               "gab_listed": GAB_LISTED }
NUMBER_ID2 = uuid.UUID('d9b15e68-5e8b-4bcf-9523-3eda4e677afd')
SIP_URI2 = "sip:5555550125@ngv.metaswitch.com"
PRIVATE_ID2 = "5555550125@ngv.metaswitch.com"
NUMBER_OBJ2 = { "number_id": NUMBER_ID2,
                "number": SIP_URI2,
                "gab_listed": GAB_LISTED }

class TestAccountsHandler(BaseTest):
    """
    Detailed, isolated unit tests of the AccountsHandler class.
    """
    def setUp(self):
        super(TestAccountsHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = users.AccountsHandler(self.app, self.request)
        self.request.arguments = copy.copy(DEFAULT_ARGUMENTS)
        arguments = self.request.arguments
        def get_argument(name, default, *args):
           return arguments[name] if name in arguments else default
        self.handler.get_argument = MagicMock(side_effect=get_argument)
        self.request.headers = {}

    @patch("metaswitch.ellis.data.users.create_user")
    def test_post_mainline(self, create_user):
        # Setup
        self.request.arguments["signup_code"] = settings.SIGNUP_CODE
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        create_user.return_value = {
             "user_id": "unique_user_id",
             "hashed_password": "hashedXXpassword",
             "full_name": FULL_NAME,
             "email": EMAIL,
             "expires": None
           }

        # Test
        self.handler.post()

        # Asserts
        create_user.assert_called_once_with(self.db_sess, PASSWORD, FULL_NAME, EMAIL, None)
        self.handler.set_status.assert_called_once_with(httplib.CREATED)
        self.handler.finish.assert_called_once_with({"username": EMAIL, "full_name": FULL_NAME})

    @patch("metaswitch.ellis.data.users.create_user")
    def test_post_mainline_header_signup(self, create_user):
        # Setup
        self.request.headers = {"NGV-Signup-Code": settings.SIGNUP_CODE}
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        create_user.return_value = {
             "user_id": "unique_user_id",
             "hashed_password": "hashedXXpassword",
             "full_name": FULL_NAME,
             "email": EMAIL,
             "expires": None
           }

        # Test
        self.handler.post()

        # Asserts
        create_user.assert_called_once_with(self.db_sess, PASSWORD, FULL_NAME, EMAIL, None)
        self.handler.set_status.assert_called_once_with(httplib.CREATED)
        self.handler.finish.assert_called_once_with({"username": EMAIL, "full_name": FULL_NAME})

    @patch("metaswitch.ellis.data.users.create_user")
    def test_post_mainline_redirect(self, create_user):
        # Setup
        self.request.arguments["signup_code"] = settings.SIGNUP_CODE
        self.request.arguments["onsuccess"] = "/success"
        self.handler.set_secure_cookie = MagicMock()
        self.handler.redirect = MagicMock()
        create_user.return_value = {
             "user_id": "unique_user_id",
             "hashed_password": "hashedXXpassword",
             "full_name": FULL_NAME,
             "email": EMAIL,
             "expires": None
           }

        # Test
        self.handler.post()

        # Asserts
        create_user.assert_called_once_with(self.db_sess, PASSWORD, FULL_NAME, EMAIL, None)
        self.handler.set_secure_cookie.assert_called_once_with("username", EMAIL)
        self.handler.redirect.assert_called_once_with("/success?data=%7B%22username%22%3A%20%22alice%40example.com%22%2C%20%22full_name%22%3A%20%22Alice%22%7D&message=Created&status=201&success=true")

    @patch("metaswitch.ellis.data.users.create_user")
    def test_post_demo(self, create_user):
        # Setup
        self.request.arguments["signup_code"] = settings.SIGNUP_CODE
        self.request.arguments["expires"] = "7"
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        create_user.return_value = {
             "user_id": "unique_user_id",
             "hashed_password": "hashedXXpassword",
             "full_name": FULL_NAME,
             "email": EMAIL,
             "expires": None
           }

        # Test
        self.handler.post()

        # Asserts
        create_user.assert_called_once_with(self.db_sess, PASSWORD, FULL_NAME, EMAIL, 7)
        self.handler.set_status.assert_called_once_with(httplib.CREATED)
        self.handler.finish.assert_called_once_with({"username": EMAIL, "full_name": FULL_NAME})

    @patch("metaswitch.ellis.data.users.create_user")
    def test_post_duplicate(self, create_user):
        # Setup
        self.request.arguments["signup_code"] = settings.SIGNUP_CODE
        create_user.side_effect = AlreadyExists

        # Test
        self.assertRaises(HTTPError, self.handler.post)

    @patch("metaswitch.ellis.data.users.create_user")
    def test_post_no_signup_code(self, create_user):
        self.request.arguments = copy.copy(DEFAULT_ARGUMENTS)
        self.assertRaises(HTTPError, self.handler.post)


class TestAccountPasswordHandler(BaseTest):
    """
    Detailed, isolated unit tests of the AccountPasswordHandler class.
    """
    def setUp(self):
        super(TestAccountPasswordHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = users.AccountPasswordHandler(self.app, self.request)
        self.request.arguments = copy.copy(DEFAULT_ARGUMENTS)
        self.request.headers = {}
        self.request.body = ""

    @patch("metaswitch.ellis.mail.mail.send_recovery_message")
    @patch("metaswitch.ellis.data.users.get_details")
    @patch("metaswitch.ellis.data.users.get_token")
    def test_post_email_mainline(self, get_token, get_details, send_recovery_message):
        get_token.return_value = TOKEN
        get_details.return_value = {"full_name": FULL_NAME, "email": EMAIL}
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()

        self.handler.post(EMAIL)

        get_token.assert_called_once_with(ANY, EMAIL)
        send_recovery_message.assert_called_once_with(ANY, EMAIL, FULL_NAME, TOKEN)
        self.handler.set_status.assert_called_once_with(200)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.api.users._email_throttler")
    @patch("metaswitch.ellis.mail.mail.send_recovery_message")
    @patch("metaswitch.ellis.data.users.get_token")
    def test_post_email_throttling(self, get_token, send_recovery_message, throttler):
        get_token.return_value = TOKEN
        self.handler.set_status = MagicMock()
        self.handler.set_header = MagicMock()
        self.handler.finish = MagicMock()
        throttler.is_allowed.return_value = False
        throttler.interval_sec = 10

        # Should fail to do anything - in particular, no token set.
        with self.assertRaises(HTTPErrorEx) as em:
            self.handler.post(EMAIL)
        e = em.exception
        self.assertEquals({"Retry-After", "10"}, e.headers)
        self.assertEquals(503, e.status_code)
        self.assertEquals(get_token.call_count, 0)
        self.assertEquals(send_recovery_message.call_count, 0)

    @patch("metaswitch.ellis.mail.mail.send_recovery_message")
    @patch("metaswitch.ellis.data.users.get_token")
    def test_post_email_bad_email(self, get_token, send_recovery_message):
        get_token.side_effect = ValueError
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()

        self.handler.post(BAD_EMAIL)

        # Shouldn't send email, but should report success as normal.
        get_token.assert_called_once_with(ANY, BAD_EMAIL)
        self.assertEquals(send_recovery_message.call_count, 0)
        self.handler.set_status.assert_called_once_with(200)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_mainline(self, set_recovered_password):
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()

        self.request.headers["NGV-Recovery-Token"] = TOKEN
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = PASSWORD.encode("utf-8")
        self.handler.post(EMAIL)

        set_recovered_password.assert_called_once_with(ANY, EMAIL, TOKEN, PASSWORD)
        self.handler.set_status.assert_called_once_with(200)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_mainline_browser(self, set_recovered_password):
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()

        self.request.arguments["password"] = [PASSWORD]
        self.request.arguments["recovery_token"] = [TOKEN]
        self.handler.post(EMAIL)

        set_recovered_password.assert_called_once_with(ANY, EMAIL, TOKEN, PASSWORD)
        self.handler.set_status.assert_called_once_with(200)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_charset(self, set_recovered_password):
        """Test charset defaulting."""
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()

        self.request.headers["NGV-Recovery-Token"] = TOKEN
        self.request.headers["Content-Type"] = "text/plain"
        self.request.body = PASSWORD.encode("iso-8859-1")
        self.handler.post(EMAIL)

        set_recovered_password.assert_called_once_with(ANY, EMAIL, TOKEN, PASSWORD)
        self.handler.set_status.assert_called_once_with(200)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_charset_fail1(self, set_recovered_password):
        """Test charset defaulting."""
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        the_password = None
        def save(self, email, token, password):
            the_password = password
        set_recovered_password(side_effect=save)

        self.request.headers["NGV-Recovery-Token"] = TOKEN
        self.request.headers["Content-Type"] = "text/plain"
        # Encode with the wrong format.
        self.request.body = PASSWORD.encode("utf-8")
        self.handler.post(EMAIL)

        # Should succeed, but set the wrong password.
        set_recovered_password.assert_called_once()
        self.assertNotEqual(PASSWORD, the_password)
        self.handler.set_status.assert_called_once_with(200)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_charset_fail2(self, set_recovered_password):
        """Test charset defaulting."""
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()

        self.request.headers["NGV-Recovery-Token"] = TOKEN
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        # Encode with the wrong format.
        self.request.body = PASSWORD.encode("iso-8859-1")
        self.request.arguments["password"] = []

        # Should fail to decode.
        self.assertRaises(HTTPError, self.handler.post, EMAIL)
        self.assertEquals(set_recovered_password.call_count, 0)

    @patch("metaswitch.ellis.api.users._recover_throttler")
    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_throttling(self, set_recovered_password, throttler):
        self.handler.set_status = MagicMock()
        self.handler.set_header = MagicMock()
        self.handler.finish = MagicMock()
        throttler.is_allowed.return_value = False
        throttler.interval_sec = 100

        self.request.headers["NGV-Recovery-Token"] = TOKEN
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = PASSWORD.encode("utf-8")

        # Should fail to do anything
        with self.assertRaises(HTTPErrorEx) as em:
            self.handler.post(EMAIL)
        e = em.exception
        self.assertEquals({"Retry-After", "100"}, e.headers)
        self.assertEquals(503, e.status_code)
        self.assertEquals(set_recovered_password.call_count, 0)

    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_bad_token(self, set_recovered_password):
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        set_recovered_password.side_effect = ValueError("UT")

        self.request.headers["NGV-Recovery-Token"] = TOKEN
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = PASSWORD.encode("utf-8")

        # Should return failure
        self.assertRaises(HTTPError, self.handler.post, EMAIL)
        self.assertEquals(set_recovered_password.call_count, 1)

    @patch("metaswitch.ellis.data.users.set_recovered_password")
    def test_post_recovered_bad_email(self, set_recovered_password):
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        set_recovered_password.side_effect = NotFound

        self.request.headers["NGV-Recovery-Token"] = TOKEN
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = PASSWORD.encode("utf-8")

        # Should return failure
        self.assertRaises(HTTPError, self.handler.post, EMAIL)
        self.assertEquals(set_recovered_password.call_count, 1)

class TestAccountHandler(BaseTest):
    def setUp(self):
        super(TestAccountHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.handler = users.AccountHandler(self.app, self.request)
        self.handler.get_and_check_user_id = MagicMock(return_value=USER_ID)
        self.handler.set_status = MagicMock()
        # Finish has an important side-effect - it sets _finished to True.  If out mocked version doesn't do this, we see multiple calls to finish.
        def finish(*args):
            self.handler._finished = True
        self.handler.finish = MagicMock(side_effect=finish)

    @patch("metaswitch.ellis.data.users.delete_user")
    @patch("metaswitch.ellis.data.numbers.get_numbers")
    def test_delete_no_nums(self, get_numbers, delete_user):
        # Setup
        get_numbers.return_value = []

        # Test
        self.handler.delete(EMAIL)

        # Asserts
        self.handler.get_and_check_user_id.assert_called_once_with(EMAIL)
        delete_user.assert_called_once_with(self.db_sess, USER_ID)
        self.handler.set_status.assert_called_once_with(httplib.NO_CONTENT)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.data.users.delete_user")
    @patch("metaswitch.ellis.data.numbers.remove_owner")
    @patch("metaswitch.ellis.api.numbers.remove_public_id")
    @patch("metaswitch.ellis.data.numbers.get_numbers")
    def test_delete_two_nums(self,
                             get_numbers,
                             remove_public_id,
                             remove_owner,
                             delete_user):
        # Setup
        get_numbers.return_value = [copy.copy(NUMBER_OBJ), copy.copy(NUMBER_OBJ2)]

        # Test
        self.handler.delete(EMAIL)

        # Assert that we kick off asynchronous deletion at homestead
        self.handler.get_and_check_user_id.assert_called_once_with(EMAIL)
        remove_public_id.assert_called_with(self.db_sess,
                                            SIP_URI2,
                                            self.handler._on_delete_post_success,
                                            self.handler._on_delete_post_failure)


        # Simulate success of request.
        remove_public_id.reset_mock()
        self.handler._on_delete_post_success([Mock()])

        # Assert that we delete the second number and user locally and finish the response
        remove_public_id.assert_called_with(self.db_sess,
                                            SIP_URI,
                                            self.handler._on_delete_post_success,
                                            self.handler._on_delete_post_failure)

        self.handler._on_delete_post_success([Mock()])
        delete_user.assert_called_once_with(self.db_sess, USER_ID)
        self.handler.set_status.assert_called_once_with(httplib.NO_CONTENT)
        self.handler.finish.assert_called_once_with({})

    @patch("metaswitch.ellis.data.users.delete_user")
    @patch("metaswitch.ellis.data.numbers.remove_owner")
    @patch("metaswitch.ellis.api.numbers.remove_public_id")
    @patch("metaswitch.ellis.data.numbers.get_numbers")
    def test_delete_two_nums_fail(self,
                                  get_numbers,
                                  remove_public_id,
                                  remove_owner,
                                  delete_user):
        # Setup
        get_numbers.return_value = [copy.copy(NUMBER_OBJ), copy.copy(NUMBER_OBJ2)]

        # Test
        self.handler.delete(EMAIL)

        # Assert that we kick off asynchronous deletion at homestead
        self.handler.get_and_check_user_id.assert_called_once_with(EMAIL)
        remove_public_id.assert_called_with(self.db_sess,
                                            SIP_URI2,
                                            self.handler._on_delete_post_success,
                                            self.handler._on_delete_post_failure)

        # Simulate failure of the request.
        self.handler._on_delete_post_failure([Mock()])

        # Assert that we bin out and don't delete the number or user locally
        self.assertFalse(delete_user.called)
        self.handler.set_status.assert_called_once_with(httplib.BAD_GATEWAY)
        self.handler.finish.assert_called_once_with({"status": 502, "detail": {}, "message": "Bad Gateway", "reason": "Upstream request failed.", "error": True})


if __name__ == "__main__":
    unittest.main()
