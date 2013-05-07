#!/usr/bin/python
# -*- coding: utf-8 -*-

# @file _base.py
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

import sys
import unittest
import uuid
from mock import Mock
from tornado.web import HTTPError
from metaswitch.ellis.api import _base
from metaswitch.ellis.data  import NotFound, connection

from mock import patch, MagicMock, ANY

class BaseTest(unittest.TestCase):
    def setUp(self):
        self.db_sess = MagicMock()
        connection.Session = Mock(return_value=self.db_sess)

class TestBaseHandler(BaseTest):

    def setUp(self):
        super(TestBaseHandler, self).setUp()
        self.app = MagicMock()
        self.app._wsgi = False
        self.request = MagicMock()
        self.request.method = "GET"
        self.request.headers = {"NGV-API-Key": 'secret'}
        self.handler = _base.BaseHandler(self.app, self.request)

    def test_prepare(self):
        self.request.headers = {"NGV-API-Key": "foo"}
        self.assertRaises(HTTPError, self.handler.prepare)
        self.request.headers = {}
        self.assertRaises(HTTPError, self.handler.prepare)
        self.request.headers = {"NGV-API-Key": 'secret'}
        self.handler.prepare()

    @patch('tornado.web.RequestHandler')
    def test_write_msgpack(self, rh):
        self.handler.prepare()
        rh.write = MagicMock()
        self.request.headers["Accept"] = "application/x-msgpack"
        self.handler.write({"a": "b"})
        rh.write.assert_called_once_with(self.handler, '\x81\xa1a\xa1b')

    @patch('tornado.web.RequestHandler')
    def test_write_json(self, rh):
        self.handler.prepare()
        rh.write = MagicMock()
        self.request.headers["Accept"] = "application/json"
        data = {"a": "b"}
        self.handler.write(data)
        rh.write.assert_called_once_with(self.handler, data)

    def test_guess_mime_type(self):
        self.assertEquals(_base._guess_mime_type("{}"), "json")
        self.assertEquals(_base._guess_mime_type("[]"), "json")
        self.assertEquals(_base._guess_mime_type("[1,2,3]"), "json")
        self.assertEquals(_base._guess_mime_type("null"), "json")
        self.assertEquals(_base._guess_mime_type('{"foo":"bar"}'), "json")
        self.assertEquals(_base._guess_mime_type("a=b"), "application/x-www-form-urlencoded")
        self.assertEquals(_base._guess_mime_type("a"), "application/x-www-form-urlencoded")
        self.assertEquals(_base._guess_mime_type("a=b&c=d"), "application/x-www-form-urlencoded")

    def test_request_data_form_encoded(self):
        self.request.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.request.body = 'a=b'
        self.request.arguments = {"a": "b"}
        data = self.handler.request_data
        self.assertEquals(data, {"a": "b"})
        # Check value is cached.
        self.request.arguments = None
        data = self.handler.request_data
        self.assertEquals(data, {"a": "b"})

    def test_request_data_form_encoded_repeats(self):
        self.request.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.request.body = 'a=b&a=c'
        self.request.arguments = {"a": ("b", "c")}
        data = self.handler.request_data
        self.assertEquals(data, {"a": ("b", "c")})

    def test_request_data_json_encoded(self):
        self.request.headers["Content-Type"] = "application/json"
        self.request.body = '{"a":"b"}'
        data = self.handler.request_data
        self.assertEquals(data, {"a": "b"})

    TEST_DATA0 = "Jolly boring, eh what? "
    TEST_DATA1 = u"""»Bewahre doch vor Jammerwoch!
Die Zähne knirschen, Krallen kratzen!
Bewahr' vor Jubjub-Vogel, vor
Frumiösen Banderschntzchen!«"""
    TEST_DATA2 = u"隻手声あり、その声を聞け"

    def test_request_text_ascii(self):
        self.request.headers["Content-Type"] = "text/plain; charset=US-ASCII"
        self.request.body = self.TEST_DATA0.encode("us-ascii")
        text = self.handler.request_text
        self.assertEquals(self.TEST_DATA0, text)

    def test_request_text_latin(self):
        self.request.headers["Content-Type"] = "text/plain; charset=iso-8859-1"
        self.request.body = self.TEST_DATA1.encode("iso-8859-1")
        text = self.handler.request_text
        self.assertEquals(self.TEST_DATA1, text)

    def test_request_text_utf8(self):
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = self.TEST_DATA2.encode("utf-8")
        text = self.handler.request_text
        self.assertEquals(self.TEST_DATA2, text)

    def test_request_text_utf8_invalid(self):
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = self.TEST_DATA1.encode("iso-8859-1")
        with self.assertRaises(HTTPError) as cm:
            self.handler.request_text
        exn = cm.exception
        self.assertEqual(400, exn.status_code)

    def test_request_text_latin_default(self):
        self.request.headers["Content-Type"] = "text/plain"
        self.request.body = self.TEST_DATA1.encode("iso-8859-1")
        text = self.handler.request_text
        self.assertEquals(self.TEST_DATA1, text)

    def test_request_text_text_default(self):
        self.request.body = self.TEST_DATA1.encode("iso-8859-1")
        text = self.handler.request_text
        self.assertEquals(self.TEST_DATA1, text)

    def test_request_text_text_nonplain(self):
        self.request.headers["Content-Type"] = "text/html; charset=iso-8859-1"
        self.request.body = self.TEST_DATA1.encode("iso-8859-1")
        with self.assertRaises(HTTPError) as cm:
            self.handler.request_text
        exn = cm.exception
        self.assertEqual(415, exn.status_code)

    def test_request_text_nontext(self):
        self.request.headers["Content-Type"] = "application/json; charset=utf-8"
        self.request.body = self.TEST_DATA2.encode("utf-8")
        with self.assertRaises(HTTPError) as cm:
            self.handler.request_text
        exn = cm.exception
        self.assertEqual(415, exn.status_code)

    def test_request_text_no_body(self):
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = None
        text = self.handler.request_text
        self.assertEquals(None, text)

    def test_request_text_or_field1(self):
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = None
        text = self.handler.request_text_or_field("achtung")
        self.assertEquals(None, text)

    def test_request_text_or_field2(self):
        self.request.headers["Content-Type"] = "text/plain; charset=utf-8"
        self.request.body = "billybob"
        text = self.handler.request_text_or_field("achtung")
        self.assertEquals("billybob", text)

    def test_request_text_or_field3(self):
        self.request.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"
        self.request.body = "wotsit=thingummy"
        args = {"wotsit": "thingummy"}
        self.handler.get_argument = args.get
        self.request.body = "blahblah"
        self.handler.request.arguments["wotsit"] = ["thingummy"]
        self.assertRaises(HTTPError, self.handler.request_text_or_field, "achtung")

    def test_request_text_or_field4(self):
        self.request.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"
        self.request.body = "achtung=baby"
        args = {"achtung": "baby"}
        self.handler.get_argument = args.get
        text = self.handler.request_text_or_field("achtung")
        self.assertEquals("baby", text)

    def test_request_text_or_field5(self):
        self.request.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"
        self.request.body = "achtung=baby&wotsit=thingummy"
        args = {"achtung": "baby",
                "wotsit": "thingummy"}
        self.handler.get_argument = args.get
        text = self.handler.request_text_or_field("achtung")
        self.assertEquals("baby", text)

    @patch("metaswitch.ellis.api.validation.validate")
    def test_validate_request(self, validate):
        validate.return_value = (True, None)
        class TestHandler(_base.BaseHandler):
            def get(self):
                pass
            get.validation = "foo"
        th = TestHandler(self.app, self.request)
        th.validate_request()

    @patch("metaswitch.ellis.api.validation.validate")
    def test_validate_request_fail(self, validate):
        validate.return_value = (False, "foo")
        class TestHandler(_base.BaseHandler):
            def get(self):
                pass
            get.validation = "foo"
        th = TestHandler(self.app, self.request)
        self.assertRaises(HTTPError, th.validate_request)

    def test_auth_assertion(self):
        self.handler.__auth_checked = False
        self.assertRaises(HTTPError, self.handler.write, {})

    def test_bad_status_code_error(self):
        self.handler.send_error = MagicMock()
        e = HTTPError(799)
        self.handler._handle_request_exception(e)
        self.handler.send_error.assert_called_once_with(500, exc_info=ANY, exception=e)

    def test_uncaught_exception(self):
        self.handler.send_error = MagicMock()
        e = Exception("uncaught")
        self.handler._handle_request_exception(e)
        self.handler.send_error.assert_called_once_with(500, exc_info=ANY, exception=e)

    def test_send_success_redirect(self):
        self.handler.get_argument = MagicMock(return_value="/foo/")
        self.handler.redirect = MagicMock()
        self.handler.send_success(200, {"foo": "bar"})
        self.handler.redirect.assert_called_once_with(
            '/foo/?data=%7B%22foo%22%3A%20%22bar%22%7D&message=OK&status=200&success=true')

    def test_send_success_non_redirect(self):
        self.handler.get_argument = MagicMock(return_value=None)
        self.handler.set_status = MagicMock()
        self.handler.finish = MagicMock()
        self.handler.send_success(200, {"foo": "bar"})
        self.handler.set_status.assert_called_once_with(200)
        self.handler.finish.assert_called_once_with({"foo": "bar"})

    def test_send_error_redirect(self):
        self.handler.get_argument = MagicMock(return_value="/foo/")
        self.handler.redirect = MagicMock()
        self.handler.send_error(400, {"foo": "bar"})
        self.handler.redirect.assert_called_once_with(
            '/foo/?detail=%7B%7D&error=true&message=Bad%20Request&'
            'reason=%7B%27foo%27%3A%20%27bar%27%7D&status=400')

    def test_write_error_debug(self):
        self.app.settings.get = MagicMock(return_value=True)
        self.handler.finish = MagicMock()
        try:
            raise Exception()
        except Exception:
            exc_info = sys.exc_info()
            self.handler.write_error(500, exc_info=exc_info)
        data = self.handler.finish.call_args[0][0]
        self.assertTrue("exception" in data)
        self.assertTrue("Traceback" in "".join(data['exception']), data["exception"])

SIP_URI = "sip:1234567890@cw-ngv.com"
OWNER_ID = uuid.uuid4()

class TestLoggedInHandler(BaseTest):

    def setUp(self):
        super(TestLoggedInHandler, self).setUp()
        self.app = MagicMock()
        self.request = MagicMock()
        self.request.method = "GET"
        self.request.headers = {"NGV-API-Key": 'secret'}
        self.handler = _base.LoggedInHandler(self.app, self.request)

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    def test_logged_in_username(self, lookup_user_id):
        lookup_user_id.return_value = OWNER_ID
        self.handler.get_secure_cookie = MagicMock(return_value="user1")
        username = self.handler.logged_in_username
        self.assertEqual(username, "user1")
        username = self.handler.logged_in_username
        self.assertEqual(username, "user1")
        self.handler.get_secure_cookie.assert_called_once_with("username")
        lookup_user_id.assert_called_once_with(self.db_sess, "user1")

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    def test_logged_in_username_not_found(self, lookup_user_id):
        lookup_user_id.side_effect = NotFound()
        self.handler.get_secure_cookie = MagicMock(return_value="user1")
        username = self.handler.logged_in_username
        self.assertEqual(username, None)

    @patch("metaswitch.ellis.data.numbers.get_sip_uri_owner_id")
    def test_check_number_ownership_found(self, get_owner):
        get_owner.return_value = OWNER_ID
        self.handler.check_number_ownership(SIP_URI, OWNER_ID)

    @patch("metaswitch.ellis.data.numbers.get_sip_uri_owner_id")
    def test_check_number_ownership_not_found(self, get_owner):
        get_owner.side_effect = NotFound()
        self.assertRaises(HTTPError,
                          self.handler.check_number_ownership, SIP_URI, OWNER_ID)

    @patch("metaswitch.ellis.data.numbers.get_sip_uri_owner_id")
    def test_check_number_ownership_different_user(self, get_owner):
        get_owner.return_value = uuid.uuid4()
        self.assertRaises(HTTPError,
                          self.handler.check_number_ownership, SIP_URI, OWNER_ID)

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    def test_is_req_authed(self, lookup_user_id):
        self.handler.get_secure_cookie = MagicMock(return_value="foo")
        self.assertTrue(self.handler.is_request_authenticated())

    @patch("metaswitch.ellis.data.users.lookup_user_id")
    def test_is_req_authed_no(self, lookup_user_id):
        lookup_user_id.side_effect = NotFound()
        self.handler.get_secure_cookie = MagicMock(return_value="foo")
        self.assertFalse(self.handler.is_request_authenticated())

class TestUnknownApiHandler(BaseTest):

    def setUp(self):
        super(TestUnknownApiHandler, self).setUp()
        self.app = MagicMock()
        self.request = MagicMock()
        self.handler = _base.UnknownApiHandler(self.app, self.request)

    def test_get(self):
        self.handler.send_error = MagicMock()
        self.handler.get()
        self.handler.send_error.assert_called_once_with(404)

if __name__ == "__main__":
    unittest.main()
