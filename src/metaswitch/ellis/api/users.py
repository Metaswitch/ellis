# @file users.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

"""
RequestHandlers for dealing with user signup and management.
"""

import logging
import httplib

from tornado.web import HTTPError, asynchronous

from metaswitch.common.throttler import Throttler

from metaswitch.ellis.api import _base
from metaswitch.ellis.api import numbers as api_numbers
from metaswitch.ellis.api._base import HTTPErrorEx
from metaswitch.ellis.api.validation import REQUIRED, OPTIONAL, STRING, validate
from metaswitch.ellis.data import users, numbers
from metaswitch.ellis.data import AlreadyExists, NotFound
from metaswitch.ellis.mail import mail
from metaswitch.ellis import settings

_log = logging.getLogger("ellis.api")

_email_throttler = Throttler(settings.THROTTLER_EMAIL_RATE_PER_SECOND,
                             settings.THROTTLER_EMAIL_BURST)
_recover_throttler = Throttler(settings.THROTTLER_RECOVER_RATE_PER_SECOND,
                               settings.THROTTLER_RECOVER_BURST)

_PASSWORD_REGEXP = r'.{6,}'

class AccountsHandler(_base.BaseHandler):
    def authenticate_request(self): # pragma: no cover
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
            db_sess.rollback()
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
    def authenticate_request(self): # pragma: no cover
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
        except ValueError:
            # To avoid revealing who subscribes to our service to
            # third parties, this must behave identically to the case
            # where the email is recognised.
            db_sess.rollback()
            _log.info("Silently ignoring unrecognised email")
        else:
            db_sess.commit()
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
        if not ok: # pragma: no cover
            raise HTTPError(httplib.BAD_REQUEST, "Password not acceptable")
        db_sess = self.db_session()
        try:
            users.set_recovered_password(db_sess, address, token, password)
            db_sess.commit()
        except (ValueError, NotFound):
            # Wrong token or unknown email address - for security reasons, these
            # must behave identically.
            db_sess.rollback()
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
            api_numbers.remove_public_id(self.db_session(), self._numbers.pop()["number"],
                                         self._on_delete_post_success, self._on_delete_post_failure, True)
        else:
            _log.debug("Deleting user %s", self._user_id)
            db_sess = self.db_session()
            users.delete_user(db_sess, self._user_id)
            db_sess.commit()
            self.send_success(httplib.NO_CONTENT)

    def _on_delete_post_success(self, responses):
        _log.debug("Successfully updated all the backends for %s", self._sip_uri)
        # We've updated all the backends, so delete the next number
        self._do_delete_work()

    def _on_delete_post_failure(self, response):
        _log.warn("Failed to update all the backends for %s", self._sip_uri)
        # Bin out.  We will end up leaving some backends with data, but the number
        # will still be owned by this user, so they can try deleting again.
        self.forward_error(response)
