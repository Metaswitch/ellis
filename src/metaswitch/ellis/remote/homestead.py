# @file homestead.py
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

def associated_uris_url(private_id, public_id=None):
    encoded_private_id = urllib.quote_plus(private_id)
    url = url_prefix() + "associateduris/%s" % (encoded_private_id)
    if public_id:
        encoded_public_id = urllib.quote_plus(public_id)
        url += "/%s" % (encoded_public_id)
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

def get_associated_uris(private_id, callback):
    """
    Retreives the associated public identities for a given private identity
    from Homestead.
    callback receives the HTTPResponse object.
    """
    url = associated_uris_url(private_id)
    fetch(url, callback, method='GET')

def post_associated_uri(private_id, public_id, callback):
    """
    Posts a new public identity to associate with a given private identity
    to Homestead.
    callback receives the HTTPResponse object.
    """
    url = associated_uris_url(private_id)
    body = urllib.urlencode({"public_id" : public_id})
    fetch(url, callback, method='POST', body=body)

def delete_associated_uri(private_id, public_id, callback):
    """
    Deletes an association between a public and private identity in Homestead
    callback receives the HTTPResponse object.
    """
    url = associated_uris_url(private_id, public_id)
    fetch(url, callback, method='DELETE')

def delete_associated_uris(private_id, callback):
    """
    Deletes all associations between public and private
    identities for the given private identity in Homestead
    callback receives the HTTPResponse object.
    """
    url = associated_uris_url(private_id)
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

