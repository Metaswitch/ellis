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

import unittest
import json
import datetime
from tornado.httpclient import HTTPError
from mock import MagicMock, Mock, patch, ANY, call
from metaswitch.ellis.remote import homestead

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

class MockHTTPClientEmptyResponse(object):
    def fetch(self, url, *args, **kwargs):
        response = Mock()
        # Imitate a tornado.httpclient.httpresponse
        response.body = '{"associated_implicit_registration_sets": []}'
        return response

class TestHomestead(unittest.TestCase):
    """
    Detailed, isolated unit tests of the homestead module.
    """

    def standard_setup(self, settings, AsyncHTTPClient):
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
        homestead.ping()
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", ANY)
        mock_response = MagicMock()
        mock_response.body = "OK"
        self.mock_httpclient.fetch.call_args[0][1](mock_response)


    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_ping_fail(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        homestead.ping()
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", ANY)
        mock_response = MagicMock()
        mock_response.body = "Failure"
        self.mock_httpclient.fetch.call_args[0][1](mock_response)


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
            ANY,
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
            ANY,
            method='PUT',
            body=body,
            headers={'Content-Type': 'application/json'},
            follow_redirects=False,
            allow_ipv6=True)

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_put_password_plaintext(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        body = json.dumps({"plaintext_password": "pw", "realm": "realm"})
        callback = Mock()
        homestead.put_password(PRIVATE_URI, "realm", "pw", callback, plaintext=True)
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/private/pri%40foo.bar',
            ANY,
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
            ANY,
            method='DELETE',
            follow_redirects=False,
            allow_ipv6=True)

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClientEmptyResponse)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_delete_private_id_no_irs(self, settings, AsyncHTTPClient):
        """Test that trying to delete a private id that has no associated IRS
           will still result in a DELETE being sent.
        """
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.delete_private_id(PRIVATE_URI, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/private/pri%40foo.bar',
            ANY,
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
            ANY,
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
        # The public ID itself is deleted synchronously - we don't
        # have infrastructure to test that yet
        self.mock_httpclient.fetch.assert_called_once_with(
          'http://homestead/irs/irs-uuid/service_profiles/sp-uuid',
            ANY,
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
            ANY,
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
            ANY,
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
                                                           ANY,
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
                                                           ANY,
                                                           method="PUT",
                                                           body='<xml />',
                                                           follow_redirects=False,
                                                           allow_ipv6=True)


class TestHomesteadBulkPublicIDs(TestHomestead):

    @patch("tornado.httpclient.HTTPClient", new=MockHTTPClient)
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_get_bulk_public_ids(self, settings, AsyncHTTPClient):
        self.standard_setup(settings, AsyncHTTPClient)
        callback = Mock()
        homestead.get_public_ids(1, 256, False, callback)
        self.mock_httpclient.fetch.assert_called_once_with(
            'http://homestead/public/?excludeuuids=false&chunk-proportion=256&chunk=1',
            ANY,
            method="GET",
            follow_redirects=False,
            allow_ipv6=True)


class TestHomesteadAsyncRetryOnOverload(TestHomestead):

    def setup_and_do_initial_request(self, settings, AsyncHTTPClient, IOLoop):
        self.standard_setup(settings, AsyncHTTPClient)
        self.mock_ioloop = Mock()
        IOLoop.return_value = self.mock_ioloop
        self.callback = Mock()
        homestead._http_request("http://homestead/ping", self.callback)

    def expect_fetch_and_respond_with(self, code):
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", ANY, follow_redirects=False, allow_ipv6=True)
        internal_callback = self.mock_httpclient.fetch.call_args[0][1]
        self.mock_httpclient.reset_mock()
        mock_response = MagicMock()
        mock_response.code = code
        internal_callback(mock_response)
        return mock_response

    def expect_timeout_set_and_call_it(self):
        self.mock_ioloop.add_timeout.assert_called_once_with(datetime.timedelta(milliseconds=500), ANY)
        timeout_callback = self.mock_ioloop.add_timeout.call_args[0][1]
        self.mock_ioloop.reset_mock()
        timeout_callback()

    @patch("tornado.ioloop.IOLoop.instance")
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_succeed_first_time(self, settings, AsyncHTTPClient, IOLoop):
        self.setup_and_do_initial_request(settings, AsyncHTTPClient, IOLoop)
        mock_response = self.expect_fetch_and_respond_with(200)
        self.callback.assert_called_once_with(mock_response)

    @patch("tornado.ioloop.IOLoop.instance")
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_fail_first_time(self, settings, AsyncHTTPClient, IOLoop):
        self.setup_and_do_initial_request(settings, AsyncHTTPClient, IOLoop)
        mock_response = self.expect_fetch_and_respond_with(500)
        self.callback.assert_called_once_with(mock_response)

    @patch("tornado.ioloop.IOLoop.instance")
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_retry_then_succeed(self, settings, AsyncHTTPClient, IOLoop):
        self.setup_and_do_initial_request(settings, AsyncHTTPClient, IOLoop)
        self.expect_fetch_and_respond_with(503)
        self.expect_timeout_set_and_call_it()
        mock_response = self.expect_fetch_and_respond_with(200)
        self.callback.assert_called_once_with(mock_response)

    @patch("tornado.ioloop.IOLoop.instance")
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.homestead.settings")
    def test_retry_until_limit(self, settings, AsyncHTTPClient, IOLoop):
        self.setup_and_do_initial_request(settings, AsyncHTTPClient, IOLoop)
        self.expect_fetch_and_respond_with(503)
        self.expect_timeout_set_and_call_it()
        self.expect_fetch_and_respond_with(503)
        self.expect_timeout_set_and_call_it()
        mock_response = self.expect_fetch_and_respond_with(503)
        self.callback.assert_called_once_with(mock_response)


class TestHomesteadSyncRetryOnOverload(TestHomestead):

    def setup_httpclient(self, HTTPClient):
        self.mock_httpclient = Mock()
        HTTPClient.return_value = self.mock_httpclient

    @patch("time.sleep")
    @patch("tornado.httpclient.HTTPClient")
    def test_succeed_first_time(self, HTTPClient, sleep):
        self.setup_httpclient(HTTPClient)
        self.mock_httpclient.fetch.return_value = "OK"
        self.assertEqual(homestead._sync_http_request("http://homestead/ping"), "OK")
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", follow_redirects=False, allow_ipv6=True)
        sleep.assert_not_called()

    @patch("time.sleep")
    @patch("tornado.httpclient.HTTPClient")
    def test_fail_first_time(self, HTTPClient, sleep):
        self.setup_httpclient(HTTPClient)
        self.mock_httpclient.fetch.side_effect = HTTPError(303, response="303 response")
        self.assertEqual(homestead._sync_http_request("http://homestead/ping"), "303 response")
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", follow_redirects=False, allow_ipv6=True)
        sleep.assert_not_called()

    @patch("time.sleep")
    @patch("tornado.httpclient.HTTPClient")
    def test_fail_exception(self, HTTPClient, sleep):
        self.setup_httpclient(HTTPClient)
        self.mock_httpclient.fetch.side_effect = Exception()
        self.assertEqual(homestead._sync_http_request("http://homestead/ping").code, 500)
        self.mock_httpclient.fetch.assert_called_once_with("http://homestead/ping", follow_redirects=False, allow_ipv6=True)
        sleep.assert_not_called()

    @patch("time.sleep")
    @patch("tornado.httpclient.HTTPClient")
    def test_retry_until_limit(self, HTTPClient, sleep):
        self.setup_httpclient(HTTPClient)
        e = HTTPError(503)
        self.mock_httpclient.fetch.side_effect = e
        self.assertEqual(homestead._sync_http_request("http://homestead/ping"), e)
        self.assertEqual(sleep.call_args_list, [call(0.5)] * 2)
        self.assertEqual(self.mock_httpclient.fetch.call_args_list,
                         [call("http://homestead/ping", follow_redirects=False, allow_ipv6=True)] * 3)


if __name__ == "__main__":
    unittest.main()
