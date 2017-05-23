# @file __init__.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


from tornado.web import RequestHandler

from metaswitch.ellis.api import users, static, session, numbers, _base
from metaswitch.ellis import settings

PATH_PREFIX = "^/"

# TODO More precise regexes
PRIVATE_ID = r'[^/]+'
PUBLIC_ID = r'[^/]+'

class PingHandler(RequestHandler):
    def get(self):
        self.finish("OK") # pragma: no cover

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
