# @file static.py
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


import re
import logging
from tornado.web import StaticFileHandler
from metaswitch.ellis.api._base import UsernameCookieMixin

_log = logging.getLogger("ellis.api")

class AuthenticatedStaticFileHandler(StaticFileHandler, UsernameCookieMixin):
    """An enhancement to Tornado's StaticFileHandler that supports restricting
    access to certain files.

    To map a path to this handler for a static data directory /var/www,
    you would add a line to your application like::

        application = web.Application([
            (r"/static/(.*)", web.StaticFileHandler, {"path": "/var/www",
                                                      "login_url": "/login.html",
                                                      "allowed_regexes": (....)}),
        ])

    The local root directory of the content should be passed as the "path"
    argument to the handler.

    To support aggressive browser caching, if the argument "v" is given
    with the path, we set an infinite HTTP expiration header. So, if you
    want browsers to cache a file indefinitely, send them to, e.g.,
    /static/images/myimage.png?v=xxx. Override ``get_cache_time`` method for
    more fine-grained cache control.
    """

    def initialize(self, path, default_filename=None,
                                login_url=None,
                                allowed_regexes=None):
        super(AuthenticatedStaticFileHandler, self).initialize(path, default_filename)
        self.login_url = login_url
        self.allowed_regexes = allowed_regexes

    def get(self, path, **kwargs):
        if self.path_is_restricted(path) and not self.request_is_authenticated():
            self.redirect_to_login_page()
            return
        super(AuthenticatedStaticFileHandler, self).get(path, **kwargs)

    def path_is_restricted(self, path):
        _log.debug("Checking if %s is allowed", path)
        path = "/%s" % path
        if path == self.login_url:
            _log.debug("Path is login path, allowed.")
            return False
        for r in self.allowed_regexes:
            if re.match(r, path):
                _log.debug("Path matches regex %s, allowed", r)
                return False
        return True

    def authenticate_request(self):
        # FIXME A bit messy
        pass

    def request_is_authenticated(self):
        return self.logged_in_username is not None

    def redirect_to_login_page(self):
        _log.debug("Redirecting to %s", self.login_url)
        self.redirect(self.login_url, False)
