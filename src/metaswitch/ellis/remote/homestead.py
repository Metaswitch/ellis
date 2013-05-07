# @file homestead.py
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


import logging
import urllib
import json

from tornado.web import HTTPError
from tornado import httpclient

from metaswitch.ellis import settings
from metaswitch.common import utils

_log = logging.getLogger("ellis.remote")

def ping():
    """Make sure we can reach homestead"""
    homestead_client = httpclient.AsyncHTTPClient()
    if settings.ALLOW_HTTP:
        scheme = "http"
    else:
        scheme = "https"
    url = "%s://%s/ping" % (scheme, settings.HOMESTEAD_URL)
    def callback(response):
        if response.body == "OK":
            _log.info("Pinged Homestead OK")
        else:
            # Shouldn't happen, as if we can reach the server, it should respond with OK
            # If it doesn't assume we've reached the wrong machine
            _log.error("Failed to ping Homestead at %s. Have you configured your HOMESTEAD_URL?" % url)
    homestead_client.fetch(url, callback)

def fetch(url, callback, **kwargs):
    http_client = httpclient.AsyncHTTPClient()
    http_client.fetch(url, callback, **kwargs)

def url_prefix():
    if settings.ALLOW_HTTP:
        scheme = "http"
        _log.warn("Passing SIP password in the clear over http")
    else:
        scheme = "https"
    url = "%s://%s/" % \
            (scheme, settings.HOMESTEAD_URL)
    return url

def digest_url(private_id, public_id):
    encoded_private_id = urllib.quote_plus(private_id)
    encoded_public_id = urllib.quote_plus(public_id)
    url = url_prefix() + ("credentials/%s/%s/digest" %
                                       (encoded_private_id, encoded_public_id))
    return url

def filter_url(public_id):
    encoded_public_id = urllib.quote_plus(public_id)
    url = url_prefix() + "filtercriteria/%s" % (encoded_public_id)
    return url

def get_digest(private_id, public_id, callback):
    """
    Retreives a digest from Homestead for a given private & public id pair
    callback receives the HTTPResponse object. Note the homestead api returns
    {"digest": "<digest>"}, rather than just the digest
    """
    url = digest_url(private_id, public_id)
    fetch(url, callback, method='GET')

def post_password(private_id, public_id, password, callback):
    """
    Posts a new password to Homestead for a given private & public id pair
    callback receives the HTTPResponse object.
    """
    url = digest_url(private_id, public_id)
    digest = utils.md5("%s:%s:%s" % (private_id, settings.SIP_DIGEST_REALM, password))
    body = urllib.urlencode({"digest" : digest})
    fetch(url, callback, method='POST', body=body)

def delete_password(private_id, public_id, callback):
    """
    Deletes a password from Homestead for a given private & public id pair
    callback receives the HTTPResponse object.
    """
    url = digest_url(private_id, public_id)
    fetch(url, callback, method='DELETE')

def get_filter_criteria(public_id, callback):
    """
    Retrieves the filter criteria associated with the given public ID.
    """
    url = filter_url(public_id)
    fetch(url, callback, method='GET')

def put_filter_criteria(public_id, ifcs, callback):
    """
    Updates the initial filter criteria in Homestead for the given line.
    callback receives the HTTPResponse object.
    """
    url = filter_url(public_id)
    headers = {"Content-Type": "application/json"}
    fetch(url, callback, method='PUT', headers=headers, body=ifcs)

def delete_filter_criteria(public_id, callback):
    """
    Deletes the filter criteria associated with the given public ID.
    """
    url = filter_url(public_id)
    fetch(url, callback, method='DELETE')

