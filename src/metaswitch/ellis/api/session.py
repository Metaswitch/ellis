# @file session.py
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
RequestHandler for creating a session.
"""

import logging
import httplib

from metaswitch.ellis.api import _base
from metaswitch.ellis.api.validation import REQUIRED, STRING
from metaswitch.ellis.data import users

_log = logging.getLogger("ellis.api")

class SessionHandler(_base.BaseHandler):
    def authenticate_request(self):
        pass

    def post(self):
        username = self.request_data["username"]
        password = self.request_data["password"]
        user = users.get_user_by_email_and_password(self.db_session(), username, password)
        if user:
            _log.debug("User %s provided correct password (%s) (%s)", username, user["email"], str(user))
            self.do_login(user, True)
        else:
            _log.debug("User %s provided incorrect password", username)
            self.send_error(httplib.FORBIDDEN, reason="Incorrect username or password")
    post.validation = {
        "username": (REQUIRED, STRING, r'.+'),
        "password": (REQUIRED, STRING, r'.+'),
    }
