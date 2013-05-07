# @file users.py
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

"""
RequestHandlers for dealing with user signup and management.
"""

import logging
import httplib

from tornado.web import HTTPError, asynchronous

from metaswitch.common.throttler import Throttler

from metaswitch.ellis.api import _base
from metaswitch.ellis.api._base import HTTPErrorEx
from metaswitch.ellis.api.utils import HTTPCallbackGroup
from metaswitch.ellis.api.validation import REQUIRED, OPTIONAL, STRING, validate
from metaswitch.ellis.data import users, numbers
from metaswitch.ellis.data import AlreadyExists, NotFound
from metaswitch.ellis.mail import mail
from metaswitch.ellis import settings
from metaswitch.ellis.remote import homestead
from metaswitch.ellis.remote import xdm
from metaswitch.common import utils

_log = logging.getLogger("ellis.api")

_email_throttler = Throttler(settings.THROTTLER_EMAIL_RATE_PER_SECOND,
                             settings.THROTTLER_EMAIL_BURST)
_recover_throttler = Throttler(settings.THROTTLER_RECOVER_RATE_PER_SECOND,
                               settings.THROTTLER_RECOVER_BURST)

_PASSWORD_REGEXP = r'.{6,}'

class AccountsHandler(_base.BaseHandler):
    def authenticate_request(self):
        # Do not require the API key for these calls.
        pass

    def post(self):
        """Create a new account."""
        _log.info("Request to create new account")
        signup_code = self.header_or_field("NGV-Signup-Code", "signup_code")
        if signup_code != settings.SIGNUP_CODE:
            _log.warning("Request had wrong/missing signup code %s", signup_code)
            raise HTTPError(httplib.FORBIDDEN, "Missing signup code")
        data = self.request_data
        db_sess = self.db_session()
        try:
            user = users.create_user(db_sess,
                                     data["password"],
                                     data["full_name"], data["email"],
                                     int(data["expires"]) if "expires" in data else None)
        except AlreadyExists:
            raise HTTPError(httplib.CONFLICT, "Email already exists")
        else:
            db_sess.commit()
            self.do_login(user)

    post.validation = {
            "password": (REQUIRED, STRING, _PASSWORD_REGEXP),
            "full_name": (REQUIRED, STRING, r'.*'),
            "email": (REQUIRED, STRING, r'[\w.]+@[\w.]+\w'),
            "expires": (OPTIONAL, STRING, r'[0-9]+'),
        }

class AccountPasswordHandler(_base.BaseHandler):
    def authenticate_request(self):
        # Do not require the API key for these calls.
        pass

    def post(self, address):
        """Recover or set password."""
        _log.info("Request to recover or set password for %s", address)
        token = self.header_or_field("NGV-Recovery-Token","recovery_token")
        if token:
            self._set_recovered_password(address, token)
        else:
            self._recover_password(address)

    def _recover_password(self, address):
        """Email a recovery token for the user."""
        _log.info("Recover password for %s", address)
        if not _email_throttler.is_allowed():
            _log.warn("Throttling to avoid being blacklisted")
            raise HTTPErrorEx(httplib.SERVICE_UNAVAILABLE, "Request throttled", headers={"Retry-After", str(_email_throttler.interval_sec)})
        db_sess = self.db_session()
        try:
            token = users.get_token(db_sess, address)
            db_sess.commit()
        except ValueError:
            # To avoid revealing who subscribes to our service to
            # third parties, this must behave identically to the case
            # where the email is recognised.
            _log.info("Silently ignoring unrecognised email")
        else:
            user = users.get_details(db_sess, address)
            urlbase = self.request.protocol + "://" + self.request.host + \
                settings.EMAIL_RECOVERY_PATH
            mail.send_recovery_message(urlbase, user["email"], user["full_name"], token)
        self.send_success(httplib.OK)

    def _set_recovered_password(self, address, token):
        """Set the password based on a recovery token."""
        _log.info("Set recovery password for %s (token %s)", address, token)
        if not _recover_throttler.is_allowed():
            _log.warn("Throttling to avoid brute-force attacks")
            raise HTTPErrorEx(httplib.SERVICE_UNAVAILABLE, "Request throttled", headers={"Retry-After", str(_recover_throttler.interval_sec)})
        password = self.request_text_or_field("password")
        ok, msg = validate({"password": password}, {"password": (REQUIRED, STRING, _PASSWORD_REGEXP)})
        if not ok:
            raise HTTPError(httplib.BAD_REQUEST, "Password not acceptable")
        db_sess = self.db_session()
        try:
            users.set_recovered_password(db_sess, address, token, password)
            db_sess.commit()
        except ValueError as e:
            # Wrong token.
            raise HTTPError(httplib.UNPROCESSABLE_ENTITY, "Invalid token or email address")
        except NotFound:
            # Unknown email address - for security reasons, this must
            # behave identically to the case where the email is
            # recognised.
            raise HTTPError(httplib.UNPROCESSABLE_ENTITY, "Invalid token or email address")
        self.send_success(httplib.OK)

class AccountHandler(_base.LoggedInHandler):
    def __init__(self, application, request, **kwargs):
        super(AccountHandler, self).__init__(application, request, **kwargs)
        self._request_group = None
        self._user_id = None
        self._numbers = None
        self._sip_uri = None

    @asynchronous
    def delete(self, email):
        _log.info("Request to delete account")
        self._user_id = self.get_and_check_user_id(email)
        self._numbers = numbers.get_numbers(self.db_session(), self._user_id)
        self._do_delete_work()

    def _do_delete_work(self):
        # If there are still numbers to delete, do so.  If not, delete the user and return.
        if len(self._numbers) > 0:
            self._delete_number_remote(self._numbers.pop()["number"])
        else:
            _log.debug("Deleting user %s", self._user_id)
            db_sess = self.db_session()
            users.delete_user(db_sess, self._user_id)
            db_sess.commit()
            self.send_success(httplib.NO_CONTENT)

    def _delete_number_remote(self, sip_uri):
        _log.debug("Removing %s from all backends", sip_uri)
        self._sip_uri = sip_uri
        self._request_group = HTTPCallbackGroup(self._on_delete_post_success,
                                                self._on_delete_post_failure)
        homestead.delete_password(utils.sip_public_id_to_private(sip_uri),
                                  sip_uri,
                                  self._request_group.callback())
        homestead.delete_filter_criteria(sip_uri, self._request_group.callback())
        xdm.delete_simservs(sip_uri, self._request_group.callback())

    def _on_delete_post_success(self, responses):
        _log.debug("Successfully updated all the backends for %s", self._sip_uri)
        # We've updated all the backends, so delete the number and do some more work.
        db_sess = self.db_session()
        numbers.remove_owner(db_sess, self._sip_uri)
        db_sess.commit()
        self._do_delete_work()

    def _on_delete_post_failure(self, response):
        _log.warn("Failed to update all the backends for %s", self._sip_uri)
        # Bin out.  We will end up leaving some backends with data, but the number
        # will still be owned by this user, so they can try deleting again.
        self.send_error(httplib.BAD_GATEWAY, reason="Upstream request failed.")
