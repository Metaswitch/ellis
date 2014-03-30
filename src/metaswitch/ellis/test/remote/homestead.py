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
import json
from mock import MagicMock, Mock, patch, ANY

from metaswitch.ellis import settings
from metaswitch.ellis.remote import homestead

from tornado import httpclient
from tornado.httputil import HTTPHeaders

PRIVATE_URI = "pri@foo.bar"
PUBLIC_URI = "sip:pub@foo.bar"
IFC_URL = "http://homestead/irs/irs-uuid/service_profiles/sp-uuid/filter_criteria"

class MockHTTPClient(object):
    def fetch(self, url, *args, **kwargs):
        response = Mock()
        # Imitate a tornado.httpclient.httpresponse
        response.body = '{"associated_implicit_registration_sets": ["abc"]}'
        response.headers.get_list.return_value = ['/irs/irs-uuid/service_profiles/sp-uuid']
        return response

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


class TestHomesteadPing(TestHomestead):

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
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


    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_ping_http(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        mock_response = MagicMock()
        mock_response.body = "OK"
        self.mock_httpclient.fetch.return_value = mock_response
        homestead.ping()
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", ANY)

class TestHomesteadPasswords(TestHomestead):

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_password(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_digest(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/private/pri%40foo.bar',
            callback,
            method='GET',
            follow_redirects=False,
            allow_ipv6=True)


    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.common.utils.md5")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_put_password_mainline(self, settings, md5, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        md5.return_value = "md5_hash"
        body = json.dumps({"digest_ha1": "md5_hash", "realm": "realm"})
        callback = Mock()
        homestead.put_password(PRIVATE_URI, "realm", "pw", callback)
        md5.assert_called_once_with("pri@foo.bar:realm:pw")
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/private/pri%40foo.bar',
            callback,
            method='PUT',
            body=body,
            headers={'Content-Type': 'application/json'},
            follow_redirects=False,
            allow_ipv6=True)

class TestHomesteadPrivateIDs(TestHomestead):
    """Tests for creating and deleting private IDs"""

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("metaswitch.common.utils.md5")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_create_private_id_mainline(self, settings, md5):
        callback = Mock()
        md5.return_value = "md5_hash"
        body = json.dumps({"digest_ha1": "md5_hash"})
        homestead.create_private_id(PRIVATE_URI, "realm", "pw", callback)

        md5.assert_called_once_with("pri@foo.bar:realm:pw")


    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_private_id_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_private_id(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/private/pri%40foo.bar',
            callback,
            method='DELETE',
            follow_redirects=False,
            allow_ipv6=True)


class TestHomesteadPublicIDs(TestHomestead):
    """Tests for creating and deleting public IDs"""

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_create_public_id_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.create_public_id(PRIVATE_URI, PUBLIC_URI, "ifcs", callback)
        self.mock_httpclient.fetch.assert_called_with(
          'http://homestead/irs/irs-uuid/service_profiles/sp-uuid/filter_criteria',
            callback,
            body="ifcs",
            method='PUT',
            follow_redirects=False,
            allow_ipv6=True)

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_public_id_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_public_id(PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/irs/irs-uuid/service_profiles/sp-uuid/public_ids/sip%3Apub%40foo.bar',
            callback,
            method='DELETE',
            follow_redirects=False,
            allow_ipv6=True)


class TestHomesteadAssociations(TestHomestead):
    """Tests for retrieving associated public/private URLs"""

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_associated_public_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_associated_publics(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/private/pri%40foo.bar/associated_public_ids',
            callback,
            method='GET',
            follow_redirects=False,
            allow_ipv6=True)

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_associated_private_mainline(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_associated_privates(PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/public/sip%3Apub%40foo.bar/associated_private_ids',
            callback,
            method='GET',
            follow_redirects=False,
            allow_ipv6=True)

class TestHomesteadiFCs(TestHomestead):

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_ifcs(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_filter_criteria(PUBLIC_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(IFC_URL,
                                                           callback,
                                                           method="GET",
                                                           follow_redirects=False,
                                                           allow_ipv6=True)

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
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
                                                           follow_redirects=False,
                                                           allow_ipv6=True)

if __name__ == "__main__":
    unittest.main()
