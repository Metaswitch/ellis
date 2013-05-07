#!/usr/bin/python

# @file xdm.py
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
from mock import patch, Mock

from metaswitch.ellis.remote import xdm

SIP_URI = "sip:1234@foo.com"
XML = """<?xml version="1.0" encoding="UTF-8"?>
<simservs xmlns="http://uri.etsi.org/ngn/params/xml/simservs/xcap" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
  <originating-identity-presentation active="true"/>
  <originating-identity-presentation-restriction active="true">
    <default-behaviour>presentation-restricted</default-behaviour>
  </originating-identity-presentation-restriction>
</simservs>"""
SIMSERVS_URL = "http://xdm/org.etsi.ngn.simservs/users/sip%3A1234%40foo.com/simservs.xml"

class TestXDM(unittest.TestCase):
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.xdm.settings")
    def test_get_simservs(self, settings, AsyncHTTPClient):
        settings.XDM_URL = "xdm"
        client = Mock()
        AsyncHTTPClient.return_value = client

        callback = Mock()
        xdm.get_simservs(SIP_URI, callback)

        client.fetch.assert_called_once_with(SIMSERVS_URL,
                                             callback,
                                             method="GET",
                                             headers={"X-XCAP-Asserted-Identity": SIP_URI})

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.xdm.settings")
    def test_put_simservs(self, settings, AsyncHTTPClient):
        settings.XDM_URL = "xdm"
        client = Mock()
        AsyncHTTPClient.return_value = client

        callback = Mock()
        xdm.put_simservs(SIP_URI, XML, callback)

        client.fetch.assert_called_once_with(SIMSERVS_URL,
                                             callback,
                                             method="PUT",
                                             body=XML,
                                             headers={"X-XCAP-Asserted-Identity": SIP_URI})

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.xdm.settings")
    def test_delete_simservs(self, settings, AsyncHTTPClient):
        settings.XDM_URL = "xdm"
        client = Mock()
        AsyncHTTPClient.return_value = client

        callback = Mock()
        xdm.delete_simservs(SIP_URI, callback)

        client.fetch.assert_called_once_with(SIMSERVS_URL,
                                             callback,
                                             method="DELETE",
                                             headers={"X-XCAP-Asserted-Identity": SIP_URI})
