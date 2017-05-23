# @file static.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


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
