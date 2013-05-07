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


from mock import patch, MagicMock, ANY, call
import unittest
import datetime

from metaswitch.ellis.data import users
from metaswitch.ellis.test.data._base import BaseDataTest
from metaswitch.ellis.data._base import AlreadyExists, NotFound

class TestUsers(BaseDataTest):

    def test_lookup_user_id(self):
        self.mock_cursor.fetchone.return_value = ("1234567890abcdefg",)
        id = users.lookup_user_id(self.mock_session, "foobar@baz.com")
        self.mock_session.execute.assert_called_once_with(ANY, {"email": "foobar@baz.com"})
        self.assertEquals(id, "1234567890abcdefg")

    def test_lookup_user_id_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.assertRaises(NotFound, users.lookup_user_id, self.mock_session, "foobar")

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    def test_create_mainline(self, lookup_user_id):
        lookup_user_id.side_effect = NotFound()
        self.mock_cursor.rowcount = 0
        user = users.create_user(self.mock_session, "password", "A User", "foo@bar.com", None)
        self.assertTrue(user["user_id"]);
        self.assertTrue(user["hashed_password"]);
        self.assertTrue(user["hashed_password"] != "password");
        self.assertEquals("A User", user["full_name"]);
        self.assertEquals("foo@bar.com", user["email"]);
        self.assertEquals(None, user["expires"]);

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    def test_create_demo_user(self, lookup_user_id):
        lookup_user_id.side_effect = NotFound()
        self.mock_cursor.rowcount = 0
        user = users.create_user(self.mock_session, "password", "A User", "foo@bar.com", 7)
        self.assertTrue(user["user_id"]);
        self.assertTrue(user["hashed_password"]);
        self.assertTrue(user["hashed_password"] != "password");
        self.assertEquals("A User", user["full_name"]);
        self.assertEquals("foo@bar.com", user["email"]);
        self.assertTrue(user["expires"]);

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    def test_create_exists(self, lookup_user_id):
        lookup_user_id.return_value = "1234567890abcfef"
        self.mock_cursor.rowcount = 1
        self.assertRaises(AlreadyExists, users.create_user,
                          self.mock_session, "password", "A User", "foo@bar.com", None)

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    @patch("metaswitch.common.utils.is_password_correct")
    def test_correct_password(self, is_pw_correct, lookup_user_id):
        is_pw_correct.return_value = True
        lookup_user_id.return_value = "1234"
        self.mock_cursor.fetchone.return_value = ["1234", "hashed", "Alice van Wonderland", "alice@example.com", 0]
        user = users.get_user_by_email_and_password(self.mock_session, "ALICE@example.com", "password")
        self.assertTrue(user)
        self.assertEquals("alice@example.com", user["email"])
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "ALICE@example.com"})
        is_pw_correct.assert_called_once_with("password", "hashed")

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    @patch("metaswitch.common.utils.is_password_correct")
    def test_incorrect_password(self, is_pw_correct, lookup_user_id):
        is_pw_correct.return_value = False
        lookup_user_id.return_value = "1234"
        self.mock_cursor.fetchone.return_value = ["1234", "hashed", "Alice van Wonderland", "alice@example.com", 0]
        user = users.get_user_by_email_and_password(self.mock_session, "user", "password")
        self.assertFalse(user)
        is_pw_correct.assert_called_once_with("password", "hashed")

    def test_delete_mainline(self):
        users.delete_user(self.mock_session, "1234567890abcfef")

    @patch("Crypto.Random.get_random_bytes")
    def test_get_token_first(self, get_random_bytes):
        self.mock_cursor.fetchone.return_value = None, None
        get_random_bytes.return_value = "\x01\x02\x41\x85\x01\x02\x41\x85\x01\x02\x41\x85\x01\x02\x41\x85"
        token = users.get_token(self.mock_session, "email@example.com")
        self.mock_session.execute.assert_has_calls([call(ANY, {'email': "email@example.com"}),
                                                    call(ANY, {'email': "email@example.com",
                                                               'token': ANY,
                                                               'created' : ANY})])
        get_random_bytes.assert_called_once_with(16)
        self.assertEquals("AQJBhQECQYUBAkGFAQJBhQ==", token)

    def test_get_token_again(self):
        self.mock_cursor.fetchone.return_value = "etaoinshrdlu", datetime.datetime.now() - datetime.timedelta(seconds=10)
        token = users.get_token(self.mock_session, "email@example.com")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "email@example.com"})
        self.assertEquals("etaoinshrdlu", token)

    @patch("Crypto.Random.get_random_bytes")
    def test_get_token_expired(self, get_random_bytes):
        self.mock_cursor.fetchone.return_value = "etaoinshrdlu", datetime.datetime.now() - datetime.timedelta(days=2)
        get_random_bytes.return_value = "\x01\x02\x41\x85\x01\x02\x41\x85\x01\x02\x41\x85\x01\x02\x41\x85"
        token = users.get_token(self.mock_session, "email@example.com")
        self.mock_session.execute.assert_has_calls([call(ANY, {'email': "email@example.com"}),
                                                    call(ANY, {'email': "email@example.com",
                                                               'token': ANY,
                                                               'created' : ANY})])
        get_random_bytes.assert_called_once_with(16)
        self.assertEquals("AQJBhQECQYUBAkGFAQJBhQ==", token)

    def test_get_token_whodat(self):
        self.mock_cursor.fetchone.side_effect = TypeError
        self.assertRaises(ValueError, users.get_token, self.mock_session, "whodat@example.com")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "whodat@example.com"})

    def test_get_user_mainline(self):
        self.mock_cursor.fetchone.return_value = ["abc123", "Maui Nukurau", "email@example.com", 123456]
        user = users.get_user(self.mock_session, "123");
        self.mock_session.execute.assert_called_once_with(ANY, {'user_id': "123"})
        self.assertEquals("123", user["user_id"])
        self.assertEquals("abc123", user["hashed_password"])
        self.assertEquals("Maui Nukurau", user["full_name"])
        self.assertEquals("email@example.com", user["email"])
        self.assertEquals(123456, user["expires"])

    def test_get_details_mainline(self):
        self.mock_cursor.fetchone.return_value = ["Maui Nukurau", "email@example.com"]
        user = users.get_details(self.mock_session, "Email@example.com")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "Email@example.com"})
        self.assertEquals("Maui Nukurau", user["full_name"])
        self.assertEquals("email@example.com", user["email"])

    def test_get_details_whodat(self):
        self.mock_cursor.fetchone.side_effect = TypeError
        self.assertRaises(ValueError, users.get_details, self.mock_session, "email@example.com")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "email@example.com"})

    def test_set_recovered_password_mainline(self):
        self.mock_cursor.fetchone.return_value = "etaoinshrdlu", datetime.datetime.now() - datetime.timedelta(seconds=10)
        users.set_recovered_password(self.mock_session, "email@example.com", "etaoinshrdlu", "newpw")
        self.mock_session.execute.assert_has_calls([call(ANY, {'email': "email@example.com"}),
                                                    call(ANY, {'email': "email@example.com",
                                                               'hashed_password': ANY})])

    def test_set_recovered_password_wrongtoken(self):
        self.mock_cursor.fetchone.return_value = "etaoinshrdlu", datetime.datetime.now() - datetime.timedelta(seconds=10)
        self.assertRaises(ValueError,
                          users.set_recovered_password,
                          self.mock_session, "email@example.com", "dunnomatey", "newpw")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "email@example.com"})

    def test_set_recovered_password_notoken(self):
        self.mock_cursor.fetchone.return_value = None, None
        self.assertRaises(NotFound,
                          users.set_recovered_password,
                          self.mock_session, "email@example.com", "dunnomatey", "newpw")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "email@example.com"})

    def test_set_recovered_password_expiredtoken(self):
        self.mock_cursor.fetchone.return_value = "etaoinshrdlu", datetime.datetime.now() - datetime.timedelta(days=2)
        self.assertRaises(NotFound,
                          users.set_recovered_password,
                          self.mock_session, "email@example.com", "dunnomatey", "newpw")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "email@example.com"})

    def test_set_recovered_password_wrongemail(self):
        self.mock_cursor.fetchone.side_effect = TypeError
        self.assertRaises(ValueError,
                          users.set_recovered_password,
                          self.mock_session, "email@example.com", "dunnomatey", "newpw")
        self.mock_session.execute.assert_called_once_with(ANY, {'email': "email@example.com"})

    def tearDown(self):
        unittest.TestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
