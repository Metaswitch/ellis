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
import re

from tornado import httpclient
from tornado.web import HTTPError

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

    def ping_callback(response):
        if response.body == "OK":
            _log.info("Pinged Homestead OK")
        else:
            # Shouldn't happen, as if we can reach the server, it should
            # respond with OK If it doesn't assume we've reached the wrong
            # machine
            _log.error("Failed to ping Homestead at %s."
                       " Have you configured your HOMESTEAD_URL?" % url)

    homestead_client.fetch(url, ping_callback)


def get_digest(private_id, callback):
    """
    Retreives a digest from Homestead for a given private id
    callback receives the HTTPResponse object. Note the homestead api returns
    {"digest_ha1": "<digest>"}, rather than just the digest
    """
    url = _private_id_url(private_id)
    _http_request(url, callback, method='GET')


def create_private_id(private_id, password, callback1, callback2):
    """Creates a private ID and associates it with an implicit
    registration set. callback1 is called when the private ID is created,
    callback2 is called when it is successfully associated with the
    implicit registration set."""
    put_password(private_id, password, callback1)
    irs_url = _new_irs_url()
    uuid = _get_irs_uuid(_location(_sync_http_request(irs_url, method="POST", body="")))
    url = _associate_new_irs_url(private_id, uuid)
    response = _sync_http_request(url, method="PUT", body="")
    callback2(response)


def put_password(private_id, password, callback):
    """
    Posts a new password to Homestead for a given private id
    callback receives the HTTPResponse object.
    """
    url = _private_id_url(private_id)
    digest = utils.md5("%s:%s:%s" % (private_id,
                                     settings.SIP_DIGEST_REALM,
                                     password))
    body = json.dumps({"digest_ha1": digest})
    headers = {"Content-Type": "application/json"}
    _http_request(url, callback, method='PUT', headers=headers, body=body)


def delete_private_id(private_id, callback):
    """
    Deletes a password from Homestead for a given private id
    callback receives the HTTPResponse object.
    """
    url = _private_id_url(private_id)
    _http_request(url, callback, method='DELETE')


def get_associated_publics(private_id, callback):
    """
    Retrieves the associated public identities for a given private identity
    from Homestead. callback receives the HTTPResponse object.
    """
    url = _associated_public_url(private_id)
    _http_request(url, callback, method='GET')


def create_public_id(private_id, public_id, callback):
    """
    Posts a new public identity to associate with a given private identity
    to Homestead.
    callback receives the HTTPResponse object.
    """
    url = _associated_irs_url(private_id)
    irs = _get_irs_uuid(_location(_sync_http_request(url, method='GET')))
    sp_url = _new_service_profile_url(irs)
    sp = _get_sp_uuid(_location(_sync_http_request(sp_url, method='POST', body="")))
    public_url = _new_public_id_url(irs, sp, public_id)
    body = "<PublicIdentity><Identity>" + \
           public_id + \
           "</Identity></PublicIdentity>"
    _http_request(public_url, callback, method='PUT', body=body)


def delete_public_id(public_id, callback):
    """
    Deletes an association between a public and private identity in Homestead
    callback receives the HTTPResponse object.
    """
    public_to_sp_url = _sp_from_public_id_url(public_id)
    response = _sync_http_request(public_to_sp_url, method='GET')
    location = _location(response)
    url = _make_url_without_prefix(location+"/public_ids/{}", public_id)
    _http_request(url, callback, method='DELETE')


def get_associated_privates(public_id, callback):
    """
    Retrieves the associated private identities for a given public identity
    from Homestead.
    callback receives the HTTPResponse object.
    """
    url = _associated_private_url(public_id)
    _http_request(url, callback, method='GET')


def get_filter_criteria(public_id, callback):
    """
    Retrieves the filter criteria associated with the given public ID.
    """
    sp_url = _sp_from_public_id_url(public_id)
    sp_location = _location(_sync_http_request(sp_url, method='GET'))
    url = _make_url_without_prefix(sp_location + "/filter_criteria")
    _http_request(url, callback, method='GET')


def put_filter_criteria(public_id, ifcs, callback):
    """
    Updates the initial filter criteria in Homestead for the given line.
    callback receives the HTTPResponse object.
    """
    sp_url = _sp_from_public_id_url(public_id)
    sp_location = _location(_sync_http_request(sp_url, method='GET'))
    url = _make_url_without_prefix(sp_location + "/filter_criteria")
    _http_request(url, callback, method='PUT', body=ifcs)


# Utility functions

def _location(httpresponse):
    """Retrieves the Location header from this HTTP response,
    throwing a 500 error if it is missing"""
    if httpresponse.headers.get_list('Location'):
        return httpresponse.headers.get_list('Location')[0]
    else:
        raise HTTPError(500)


def _http_request(url, callback, **kwargs):
    http_client = httpclient.AsyncHTTPClient()
    http_client.fetch(url, callback, **kwargs)


def _sync_http_request(url, **kwargs):
    http_client = httpclient.HTTPClient()
    return http_client.fetch(url, **kwargs)


def _url_prefix():
    if settings.ALLOW_HTTP:
        scheme = "http"
        _log.warn("Passing SIP password in the clear over http")
    else:
        scheme = "https"
    url = "%s://%s/" % \
          (scheme, settings.HOMESTEAD_URL)
    return url


def _private_id_url(private_id):
    """Returns the URL for accessing/setting/creating this private ID's
    password"""
    return _make_url("private/{}", private_id)


def _associated_public_url(private_id):
    """Returns the URL for learning this private ID's associated public IDs'"""
    return _make_url("private/{}/associated_public_ids", private_id)


def _associated_private_url(public_id):
    """Returns the URL for learning this public ID's associated private IDs'"""
    return _make_url("public/{}/associated_private_ids", public_id)


def _new_public_id_url(irs, service_profile, public_id):
    """Returns the URL for creating a new public ID in this service profile"""
    return _make_url("irs/{}/service_profiles/{}/public_ids/{}",
                     irs,
                     service_profile,
                     public_id)


def _new_irs_url():
    """Returns the URL for creating a new implicit registration set"""
    return _make_url("irs/")


def _new_service_profile_url(irs):
    """Returns the URL for creating a new service profile in this IRS"""
    return _make_url("irs/{}/service_profiles", irs)


def _associated_irs_url(private_id):
    """Returns the URL for learning this private ID's associated implicit
    registration sets"""
    return _make_url("private/{}/associated_implicit_registration_sets",
                     private_id)


def _associate_new_irs_url(private_id, irs):
    """Returns the URL for associating this private ID and IRS"""
    return _make_url("private/{}/associated_implicit_registration_sets/{}",
                     private_id,
                     irs)


def _sp_from_public_id_url(public_id):
    """Returns the URL for learning this public ID's service profile"""
    return _make_url('public/{}/service_profile', public_id)


def _make_url_without_prefix(format_str, *args):
    """Makes a URL by URL-escaping the args, and interpolating them into
    format_str"""
    formatted_args = [urllib.quote_plus(arg) for arg in args]
    return format_str.format(*formatted_args)


def _make_url(format_str, *args):
    """Makes a URL by URL-escaping the args, interpolating them into
    format_str, and adding a prefix"""
    return _url_prefix() + _make_url_without_prefix(format_str, *args)


def _get_irs_uuid(url):
    """Retrieves the UUID of an Implicit Registration Set from a URL"""
    match = re.search("irs/([^/]+)", url)
    if not match:
        return None
    return match.group(1)


def _get_sp_uuid(url):
    """Retrieves the UUID of a Service Profile from a URL"""
    mo = re.search("irs/[^/]+/service_profiles/([^/]+)", url)
    if not mo:
        print url
        return None
    return mo.group(1)
