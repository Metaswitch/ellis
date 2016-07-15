# @file utils.py
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
from tornado.httpclient import HTTPError

_log = logging.getLogger("ellis.api")

class HTTPCallbackGroup(object):
    """
    Helper class for handling multiple concurrent HTTP requests.  Provides
    a factory for callback functions and a global hook that gets called once
    the outcome of the group of requests is known.
    """

    def __init__(self, success_callback=None,
                        failure_callback=None,
                        treat_delete_404_as_success=True):
        self._success_callback = success_callback
        self._failure_callback = failure_callback
        self._live_callbacks = set()
        self._treat_delete_404_as_success = treat_delete_404_as_success
        self.responses = []

    def callback(self):
        def callback(response):
            self._live_callbacks.remove(callback)
            self.responses.append(response)
            self._check_finished(response)
        self._live_callbacks.add(callback)
        return callback

    def _response_was_successful(self, resp):
        if isinstance(resp, HTTPError): # pragma: no cover
            return False
        else:
            # We have a tornado.httpclient.HTTPResponse
            return ((resp.code // 100 == 2) or
                    (self._treat_delete_404_as_success and
                     resp.request.method == "DELETE" and
                     resp.code == 404))

    def _check_finished(self, response):
        if not self._response_was_successful(response):
            # Bad response
            _log.warning("Non-OK HTTP response. %s", response)
            if self._failure_callback:
                # Immediately report failure
                self._failure_callback(response)
                self._failure_callback = None
        else:
            _log.debug("OK HTTP response. %s", response)
            if len(self._live_callbacks) == 0:
                for r in self.responses:
                    if not self._response_was_successful(r):
                        _log.debug("Another response failed, skipping callbacks.")
                        return
                # If we get here, all responses were successful.
                if self._success_callback:
                    _log.debug("All requests successful.")
                    self._success_callback(self.responses)
        _log.debug("Still expecting %s callbacks", len(self._live_callbacks))
