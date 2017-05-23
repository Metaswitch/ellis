# @file utils.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


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
