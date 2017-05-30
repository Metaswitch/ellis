# @file session.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


"""
RequestHandler for creating a session.
"""

import logging
import httplib

from metaswitch.ellis.api import _base
from metaswitch.ellis.api.validation import REQUIRED, STRING
from metaswitch.ellis.data import users

_log = logging.getLogger("ellis.api")

class SessionHandler(_base.BaseHandler):
    def authenticate_request(self): # pragma: no cover
        pass

    def post(self):
        username = self.request_data["email"]
        password = self.request_data["password"]
        user = users.get_user_by_email_and_password(self.db_session(), username, password)
        if user:
            _log.debug("User %s provided correct password (%s) (%s)", username, user["email"], str(user))
            self.do_login(user, True)
        else:
            _log.debug("User %s provided incorrect password", username)
            self.send_error(httplib.FORBIDDEN, reason="Incorrect username or password")
    post.validation = {
        "email": (REQUIRED, STRING, r'.+'),
        "password": (REQUIRED, STRING, r'.+'),
    }
