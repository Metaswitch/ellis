#!/usr/bin/python

# @file homestead.py
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


import urllib

import unittest
from mock import MagicMock, Mock, patch, ANY

from metaswitch.ellis import settings
from metaswitch.ellis.remote import homestead

from tornado import httpclient

PRIVATE_URI = "pri@foo.bar"
PUBLIC_URI = "sip:pub@foo.bar"
IFC_URL = "http://homestead/filtercriteria/sip%3Apub%40foo.bar"

class TestHomestead(unittest.TestCase):
    """
    Detailed, isolated unit tests of the homestead module.
    """

    def standard_setup(self, settings, AsyncHTTPClient):
        settings.ALLOW_HTTP = True
        settings.HOMESTEAD_URL = "homestead"
        settings.SIP_DIGEST_REALM = "foo.bar"
        self.mock_httpclient = Mock()
        AsyncHTTPClient.return_value = self.mock_httpclient

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_ping_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        settings.ALLOW_HTTP = False
        mock_response = MagicMock()
        mock_response.body = "OK"
        self.mock_httpclient.fetch.return_value = mock_response
        homestead.ping()
        self.mock_httpclient.fetch.assert_called_once_with("https://homestead/ping", ANY)

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_ping_http(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        mock_response = MagicMock()
        mock_response.body = "OK"
        self.mock_httpclient.fetch.return_value = mock_response
        homestead.ping()
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", ANY)

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_password(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_digest(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/privatecredentials/pri%40foo.bar/digest',
          callback,
          method='GET')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.common.utils.md5")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_put_password_mainline(self, settings, md5, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        md5.return_value = "md5_hash"
        body = urllib.urlencode({"digest" : "md5_hash"})
        callback = Mock()
        homestead.put_password(PRIVATE_URI, "pw", callback)
        md5.assert_called_once_with("pri@foo.bar:%s:pw" % settings.SIP_DIGEST_REALM)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/privatecredentials/pri%40foo.bar/digest',
          callback,
          method='PUT',
          body=body)

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_password_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_password(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/privatecredentials/pri%40foo.bar/digest',
          callback,
          method='DELETE')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_associated_public_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_associated_publics(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedpublic/pri%40foo.bar',
          callback,
          method='GET')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_post_associated_public_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        body = urllib.urlencode({"public_id" : PUBLIC_URI})
        callback = Mock()
        homestead.post_associated_public(PRIVATE_URI, PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedpublic/pri%40foo.bar',
          callback,
          method='POST',
          body=body)

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_associated_public_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_associated_public(PRIVATE_URI, PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedpublic/pri%40foo.bar/sip%3Apub%40foo.bar',
          callback,
          method='DELETE')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_associated_publics_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_associated_publics(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedpublic/pri%40foo.bar',
          callback,
          method='DELETE')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_associated_private_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_associated_privates(PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedprivate/sip%3Apub%40foo.bar',
          callback,
          method='GET')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_post_associated_private_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        body = urllib.urlencode({"private_id" : PRIVATE_URI})
        callback = Mock()
        homestead.post_associated_private(PUBLIC_URI, PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedprivate/sip%3Apub%40foo.bar',
          callback,
          method='POST',
          body=body)

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_associated_private_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_associated_private(PUBLIC_URI, PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedprivate/sip%3Apub%40foo.bar/pri%40foo.bar',
          callback,
          method='DELETE')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_associated_privates_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_associated_privates(PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/associatedprivate/sip%3Apub%40foo.bar',
          callback,
          method='DELETE')

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_ifcs(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_filter_criteria(PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(IFC_URL,
                                                           callback,
                                                           method="GET")

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_put_ifcs(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.put_filter_criteria(PUBLIC_URI, '<xml />', callback)
        self.mock_httpclient.fetch.assert_called_once_with(IFC_URL,
                                                           callback,
                                                           method="PUT",
                                                           body='<xml />',
                                                           headers={'Content-Type': 'application/json'})

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_ifcs(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_filter_criteria(PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(IFC_URL,
                                                           callback,
                                                           method="DELETE")

if __name__ == "__main__":
    unittest.main()
