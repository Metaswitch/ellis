# @file __init__.py
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


from tornado.web import RequestHandler

from metaswitch.ellis.api import users, static, session, numbers, _base
from metaswitch.ellis import settings

PATH_PREFIX = "^/"

# TODO More precise regexes
PRIVATE_ID = r'[^/]+'
PUBLIC_ID = r'[^/]+'

class PingHandler(RequestHandler):
    def get(self):
        self.finish("OK")

URLS = [
    # User-focussed APIs.  Typically secured with username/password.

    # User account creation.
    # /accounts/ (POST)
    (PATH_PREFIX + r'accounts/?$', users.AccountsHandler),

    # Account edit.
    # /accounts/<account_id> (DELETE)
    (PATH_PREFIX + r'accounts/([^/]*)/?$', users.AccountHandler),
    # Recover/set password.
    # /accounts/<account_id>/password (POST)
    (PATH_PREFIX + r'accounts/([^/]*)/password/?$', users.AccountPasswordHandler),

    # Create/list SIP IDs.
    # /accounts/<account_id>/numbers
    (PATH_PREFIX + r'accounts/([^/]+)/numbers/?$', numbers.NumbersHandler),
    # Update/delete number.
    (PATH_PREFIX + r'accounts/([^/]*)/numbers/([^/]*)/?$', numbers.NumberHandler),
    # SIP password update
    (PATH_PREFIX + r'accounts/([^/]*)/numbers/([^/]*)/password/?$', numbers.SipPasswordHandler),
    # Read/write from XDM for number
    (PATH_PREFIX + r'accounts/([^/]*)/numbers/([^/]*)/simservs/?$', numbers.SimservsHandler),
    # Read/write iFCs from Homestead for number
    (PATH_PREFIX + r'accounts/([^/]*)/numbers/([^/]*)/ifcs/?$', numbers.IFCsHandler),
    # GAB availability
    (PATH_PREFIX + r'accounts/([^/]*)/numbers/([^/]*)/listed/?$', numbers.NumberGabListedHandler),
    # GAB availability update
    (PATH_PREFIX + r'accounts/([^/]*)/numbers/([^/]*)/listed/([0-1])/?$', numbers.NumberGabListedHandler),

    # Global Address Book (GAB) - allow 1/gab for back-compatibility for Android client
    (PATH_PREFIX + r'(?:1/)?gab/?$', numbers.GabListedNumbersHandler),

    # Session management.
    (PATH_PREFIX + r'session/?$', session.SessionHandler),

    # APIs for other components to access.  Typically secured using API_KEY.

    # Liveness ping.
    (PATH_PREFIX + r'ping/?$', PingHandler),

    # Static files, all but a few pages secured with a cookie.
    ("^/(.*)$", static.AuthenticatedStaticFileHandler,
               {"path": settings.STATIC_DIR,
                "default_filename": "index.html",
                "login_url": "/login.html",
                "allowed_regexes": (
                    r'/js/(jquery|backbone|underscore|fileuploader|bootstrap|login|signup|forgotpassword|resetpassword|common|zxcvbn|zxcvbn-async|pwstrength|validate).*',
                    r'/js/templates/*\.html',
                    r'/img/.*',
                    r'/css/.*',
                    r'/login\.html',
                    r'/signup\.html',
                    r'/forgotpassword\.html',
                    r'/resetpassword\.html',
                )}),

    # JSON 404 page for API calls.
    (PATH_PREFIX + r'.*$', _base.UnknownApiHandler),
]
