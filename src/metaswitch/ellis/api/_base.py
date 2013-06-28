# @file _base.py
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


import logging
import json
import traceback
import httplib
import cgi
import threading

import msgpack
import tornado.web
from tornado.web import HTTPError, RequestHandler

from metaswitch.common import utils
from metaswitch.ellis import settings
from metaswitch.ellis.api import validation
from metaswitch.ellis.data import users, numbers, connection
from metaswitch.ellis.data import NotFound
import sys

_log = logging.getLogger("ellis.api")

# Add missing responses
httplib.responses[422] = "Unprocessable Entity"

def _guess_mime_type(body):
    if (body == "null" or
        (body[0] == "{" and
         body[-1] == "}") or
        (body[0] == "[" and
         body[-1] == "]")):
        _log.warning("Guessed MIME type of uploaded data as JSON. Client should specify.")
        return "json"
    else:
        _log.warning("Guessed MIME type of uploaded data as URL-encoded. Client should specify.")
        return "application/x-www-form-urlencoded"

class DbSessionMixin(object):
    def db_session(self):
        if not hasattr(self, "_db_session"):
            self._db_session = connection.Session()
        return self._db_session

    def on_finish(self):
        super(DbSessionMixin, self).on_finish()
        if hasattr(self, "_db_session"):
            self._db_session.close()
        # @@@KSW for some reason, this isn't called if the handler throws!

class BaseHandler(tornado.web.RequestHandler, DbSessionMixin):
    """
    Base class for our web handlers, should handle shared concerns like
    authenticating requests and post-processing data.
    """

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.__request_data = None
        self.__request_text = None
        self.__auth_checked = False


    def authenticate_request(self):
        auth_header = self.request.headers.get("NGV-API-Key", None)
        # FIXME need to add username to URL and validate against that
        authentic = auth_header == settings.API_KEY or self.get_secure_cookie("username") is not None

        if not authentic:
            _log.error("Request was missing NGV-API-Key or authentication cookie.")
            raise HTTPError(403, "NGV-API-Key header or authentication cookie was missing or incorrect")

    def validate_request(self):
        # Look for declarative validation metadata.
        handler_fn = getattr(self, self.request.method.lower())
        valid = True
        reason = None
        if hasattr(handler_fn, "validation"):
            # Validate against the metadata.
            v_data = handler_fn.validation
            valid, reason = validation.validate(self.request_data, v_data)
        if not valid:
            raise HTTPError(400, reason)

    def prepare(self):
        # Defensive: make sure we spot if someone fails to call super after
        # overriding prepare().
        self.__auth_checked = True
        self.authenticate_request()
        self.validate_request()

    def write(self, chunk):
        if not self.__auth_checked:
            # Defensive: make sure we spot if someone fails to call super after
            # overriding prepare().
            _log.critical("Request wasn't authenticated by %s", self)
            raise HTTPError(500)
        if (isinstance(chunk, dict) and
            "application/x-msgpack" in self.request.headers.get("Accept", "")):
            _log.debug("Responding with msgpack")
            self.set_header("Content-Type", "application/x-msgpack")
            chunk = msgpack.dumps(chunk)
        tornado.web.RequestHandler.write(self, chunk)

    def header_or_field(self, header_name, field_name):
        """Retrieve data from HTTP header or form field."""
        ret = self.request.headers.get(header_name, None)
        if not ret:
            _log.debug("No %s code in header, looking in body", header_name)
            ret = self.get_argument(field_name, None)
        return ret

    def _query_data(self, args):
        ret = {}
        for k in args:
            if len(args[k]) == 1:
                ret[k] = args[k][0]
            else:
                ret[k] = args[k]
        return ret

    def _handle_request_exception(self, e):
        """
        Overridden to pass on the exception object to send_error.  Otherwise,
        should track superclass version.
        """
        if isinstance(e, HTTPError):
            if e.log_message:
                format = "%d %s: " + e.log_message
                args = [e.status_code, self._request_summary()] + list(e.args)
                logging.warning(format, *args)
            if e.status_code not in httplib.responses:
                logging.error("Bad HTTP status code: %d", e.status_code)
                self.send_error(500, exc_info=sys.exc_info(), exception=e)
            else:
                self.send_error(e.status_code, exc_info=sys.exc_info(), exception=e)
        else:
            logging.error("Uncaught exception %s\n%r", self._request_summary(),
                          self.request, exc_info=True)
            self.send_error(500, exc_info=sys.exc_info(), exception=e)

    @property
    def request_data(self):
        """The data parsed from the body (JSON and form encoding supported)."""
        if self.__request_data is None:
            self.__request_data = {}
            body = self.request.body
            if body:
                headers = self.request.headers
                type = headers.get("Content-Type", None)
                if type is None:
                    type = _guess_mime_type(body)
                if "json" in type:
                    self.__request_data = json.loads(body)
                else:
                    self.__request_data = self._query_data(self.request.arguments)
        return self.__request_data

    @property
    def request_text(self):
        """The text/plain content of the body.

        Insists the content type is text/plain, and extracts the
        charset if any.  Ignores all other headers and parameters
        (e.g., the transfer encoding is assumed to be 8bit).
        Doesn't handle gzip.
        """
        if self.__request_text is None:
            body = self.request.body
            if body:
                header = self.request.headers.get("Content-Type", None)
                if header is None:
                    header = "text/plain"
                    _log.warning("Guessed MIME type of uploaded data as %s. Client should specify.", header)
                content_type, params = cgi.parse_header(header)
                if 'charset' in params:
                    charset = params['charset'].strip("'\"")
                else:
                    charset = 'iso-8859-1'  # default for text/*
                    _log.warning("Guessed charset of uploaded data as %s. Client should specify.", charset)
                if content_type == "text/plain":
                    try:
                        self.__request_text = body.decode(charset)
                    except Exception as e:
                        raise HTTPError(httplib.BAD_REQUEST, e)
                    _log.debug("Decoded %s as %s: got %s", body, charset, self.__request_text)
                else:
                    raise HTTPError(httplib.UNSUPPORTED_MEDIA_TYPE,
                                    "text/plain required")
        return self.__request_text

    def request_text_or_field(self, field_name):
        """Retrieve data from request body or form field.

        Expects a text/plain body; failing that, extracts a form field.
        """
        ret = None
        try:
            ret = self.request_text
            if not ret:
                _log.debug("No body: fall back on field %s", field_name)
                ret = self.get_argument(field_name, None)
        except Exception as e:
            _log.debug("Failed (%s): fall back on field %s", e, field_name)
            ret = self.get_argument(field_name, None)
            if not ret:
                _log.debug("Ret is still %s", ret)
                raise e
        return ret

    def do_login(self, user, set_cookie=False):
        """
        Handle a successful login: if requested or we're about to
        redirect, set an auth cookie; in any case, respond or redirect
        including the necessary session information.
        """
        redirect_url = self.get_argument("onsuccess", None)
        if set_cookie or redirect_url:
            # Request from a web form: add an auth cookie.
            self.set_secure_cookie("username", user["email"])
        self.send_success(httplib.CREATED,
                          data={"username": user["email"],
                                "full_name": user["full_name"]})

    def send_success(self, status_code=200, data={}):
        """
        If the client has requested a redirect response, serializes the data
        into a redirect.  Otherwise, equivalent to:

        self.set_status(status_code)
        self.finish(data)
        """
        redirect_url = self.get_argument("onsuccess", None)
        if redirect_url:
            redirect_url = utils.append_url_params(redirect_url,
                                                   success="true",
                                                   status=status_code,
                                                   message=httplib.responses[status_code],
                                                   data=json.dumps(data))
            self.redirect(redirect_url)
        else:
            self.set_status(status_code)
            self.finish(data)

    def forward_error(self, response):
        """
        Forwards on an error from a remote backend
        """
        self.send_error(httplib.BAD_GATEWAY,
                        reason="Upstream request failed",
                        detail={"Upstream error": str(response.error)})

    def send_error(self, status_code=500, reason="unknown", detail={}, **kwargs):
        """
        Sends an error response to the client, finishing the request in the
        process.

        If the client has requested an error redirect rather than a status
        code then the error is formatted into URL parameters and sent on the
        redirect instead.
        """
        redirect_url = self.get_argument("onfailure", None)
        headers = {}
        if "exception" in kwargs:
            e = kwargs["exception"]
            if reason == "unknown" and isinstance(e, HTTPError):
                reason = e.log_message or "unknown"
            if isinstance(e, HTTPErrorEx):
                headers = e.headers
        if redirect_url:
            # The client (likely a webpage) has requested that we signal
            # failure by redirecting to a specific URL.
            redirect_url = utils.append_url_params(redirect_url,
                                                   error="true",
                                                   status=status_code,
                                                   message=httplib.responses[status_code],
                                                   reason=reason,
                                                   detail=json.dumps(detail))
            self.redirect(redirect_url)
        else:
            # Handle normally.  this will loop back through write_error below.
            tornado.web.RequestHandler.send_error(self,
                                                  status_code=status_code,
                                                  reason=reason,
                                                  detail=detail,
                                                  headers=headers,
                                                  **kwargs)

    def write_error(self, status_code, reason="unknown", detail={}, **kwargs):
        """
        Writes the error page as a JSON blob containing information about the
        error.
        """
        data = {
            "error": True,
            "status": status_code,
            "message": httplib.responses[status_code],
            "reason": reason,
            "detail": detail,
        }
        if self.settings.get("debug") and "exc_info" in kwargs:
            data["exception"] = traceback.format_exception(*kwargs["exc_info"])
        if 'headers' in kwargs:
            for k,v in kwargs['headers']:
                self.set_header(k,v)
        self.finish(data)

class UsernameCookieMixin(RequestHandler, DbSessionMixin):
    @property
    def logged_in_username(self):
        if not hasattr(self, "_username"):
            username = self.get_secure_cookie("username")
            if username != None:
                try:
                    users.lookup_user_id(self.db_session(), username)
                except NotFound:
                    username = None
            self._username = username
        return self._username

class LoggedInHandler(BaseHandler, UsernameCookieMixin):
    def check_number_ownership(self, sip_uri, user_id):
        try:
            owner_id = numbers.get_sip_uri_owner_id(self.db_session(), sip_uri)
        except NotFound:
            raise HTTPError(404, "Number not found")
        else:
            if owner_id != user_id:
                raise HTTPError(404, "User doesn't own that number")

    def get_and_check_user_id(self, username):
        if username != self.logged_in_username and \
           self.request.headers.get("NGV-API-Key", None) != settings.API_KEY:
            raise HTTPError(403, "Username doesn't match logged in username.")
        try:
            return users.lookup_user_id(self.db_session(), username)
        except NotFound:
            raise HTTPError(404, "User not found.")

    def is_request_authenticated(self):
        return self.logged_in_username is not None


class HTTPErrorEx(HTTPError):
    """An exception that will turn into an HTTP error response with headers."""
    def __init__(self, status_code, log_message=None, headers={}, *args):
        self.status_code = status_code
        self.log_message = log_message
        self.headers = headers
        self.args = args

class UnknownApiHandler(BaseHandler):
    """
    Handler that sends a 404 JSON/msgpack/etc response to all requests.
    """
    def get(self):
        self.send_error(404)
