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


import unittest
import uuid
from mock import ANY, patch
from metaswitch.ellis.data.numbers import (get_sip_uri_number_id,
                                               get_sip_uri_owner_id,
                                               remove_owner,
                                               add_number_to_pool,
                                               allocate_number,
                                               get_number,
                                               get_numbers,
                                               update_gab_list)
from metaswitch.ellis.test.data._base import BaseDataTest
from metaswitch.ellis.data import NotFound

SIP_URI = "sip:1234@foo.com"
OWNER_ID = uuid.uuid4()
NUMBER_ID = uuid.uuid4()
GAB_LISTED = 1

class TestNumbers(BaseDataTest):

    def test_get_numbers(self):
        self.mock_cursor.fetchall.return_value = [(NUMBER_ID.hex, SIP_URI, False, GAB_LISTED)]
        numbers = get_numbers(self.mock_session, OWNER_ID)
        self.assertEqual(numbers, [
            {
              "number": SIP_URI,
              "number_id": NUMBER_ID,
              "pstn": False,
              "gab_listed": GAB_LISTED
            }
        ])

    def test_get_sip_uri_owner_id(self):
        self.mock_cursor.fetchone.return_value = (OWNER_ID,)
        id = get_sip_uri_owner_id(self.mock_session, SIP_URI)
        self.mock_session.execute.assert_called_once_with(ANY, {"number": SIP_URI})
        self.assertEqual(id, OWNER_ID)

    def test_get_sip_uri_owner_id_no_owner(self):
        # Not 100% sure we'll hit this in practice
        self.mock_cursor.fetchone.return_value = (None,)
        self.assertRaises(NotFound, get_sip_uri_owner_id, self.mock_session, SIP_URI)

    def test_get_sip_uri_owner_id_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.assertRaises(NotFound, get_sip_uri_owner_id, self.mock_session, SIP_URI)

    def test_get_sip_uri_number_id(self):
        self.mock_cursor.fetchone.return_value = (NUMBER_ID,)
        id = get_sip_uri_number_id(self.mock_session, SIP_URI)
        self.mock_session.execute.assert_called_once_with(ANY, {"number": SIP_URI})
        self.assertEqual(id, NUMBER_ID)

    def test_get_sip_uri_number_id_no_owner(self):
        # Not 100% sure we'll hit this in practice
        self.mock_cursor.fetchone.return_value = (None,)
        self.assertRaises(NotFound, get_sip_uri_number_id, self.mock_session, SIP_URI)

    def test_get_sip_uri_number_id_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.assertRaises(NotFound, get_sip_uri_number_id, self.mock_session, SIP_URI)

    @patch("metaswitch.ellis.data.numbers.get_sip_uri_number_id")
    def test_remove_owner(self, get_sip_id):
        get_sip_id.return_value = NUMBER_ID
        self.mock_cursor.rowcount = 1
        remove_owner(self.mock_session, SIP_URI)
        self.mock_session.execute.assert_called_with(ANY, {"number_id": NUMBER_ID})

    @patch("metaswitch.ellis.data.numbers.add_number_to_pool")
    @patch("metaswitch.ellis.data.numbers.get_sip_uri_number_id")
    def test_remove_owner_not_found(self, get_sip_id, add_to_pool):
        get_sip_id.return_value = NUMBER_ID
        self.mock_cursor.rowcount = 0
        remove_owner(self.mock_session, SIP_URI)
        self.mock_session.execute.assert_called_with(ANY, {"number_id": NUMBER_ID})
        self.assertFalse(add_to_pool.called)

    @patch("uuid.uuid4")
    def test_add_number_to_pool(self, uuid4):
        uuid4.return_value = NUMBER_ID
        add_number_to_pool(self.mock_session, SIP_URI)
        self.mock_session.execute.assert_called_once_with(ANY,
                                                          {
                                                           "number_id": NUMBER_ID,
                                                           "number": SIP_URI,
                                                           "pstn": False,
                                                           "specified": False
                                                           })

    def test_allocate_number(self):
        self.mock_cursor.fetchone.return_value = (NUMBER_ID.hex,)
        num_id = allocate_number(self.mock_session, OWNER_ID)
        self.assertEqual(num_id, NUMBER_ID)

    def test_allocate_pstn_number(self):
        self.mock_cursor.fetchone.return_value = (NUMBER_ID.hex,)
        num_id = allocate_number(self.mock_session, OWNER_ID, True)
        self.assertEqual(num_id, NUMBER_ID)

    @patch("random.randint")
    def test_allocate_number_not_found(self, randint):
        self.mock_cursor.fetchone.return_value = (None, )
        self.assertRaises(NotFound, allocate_number, self.mock_session, OWNER_ID)

    def test_get_number(self):
        self.mock_cursor.fetchone.return_value = (SIP_URI, OWNER_ID)
        sip_uri = get_number(self.mock_session, NUMBER_ID, OWNER_ID)
        self.assertEqual(sip_uri, SIP_URI)

    def test_get_number_wrong_owner(self):
        self.mock_cursor.fetchone.return_value = (SIP_URI, uuid.uuid4())
        self.assertRaises(NotFound, get_number, self.mock_session, NUMBER_ID, OWNER_ID)

    def test_get_number_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.assertRaises(NotFound, get_number, self.mock_session, NUMBER_ID, OWNER_ID)

    def test_update_gab_list_insert_number(self):
        update_gab_list(self.mock_session, OWNER_ID, NUMBER_ID, True)
        self.mock_session.execute.assert_called_once_with(ANY,
                                                          {
                                                            "gab": True,
                                                            "nid": NUMBER_ID
                                                          })

    def test_update_gab_list_remove_number(self):
        update_gab_list(self.mock_session, OWNER_ID, NUMBER_ID, False)
        self.mock_session.execute.assert_called_once_with(ANY,
                                                          {
                                                            "gab": False,
                                                            "nid": NUMBER_ID
                                                          })

if __name__ == "__main__":
    unittest.main()
