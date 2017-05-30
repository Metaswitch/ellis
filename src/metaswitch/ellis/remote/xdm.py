# @file xdm.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import logging
import urllib

from tornado import httpclient

from metaswitch.ellis import settings

_log = logging.getLogger("ellis.remote")

def simservs_uri(user):
    encoded_user = urllib.quote(user, safe="")
    path = "org.etsi.ngn.simservs/users/%s/simservs.xml" % encoded_user
    uri = "http://%s/%s" % (settings.XDM_URL, path)
    return uri

def fetch_with_headers(user, uri, callback, **kwargs):
    _log.info("Sending HTTP %s request to %s",
              kwargs.get('method', 'GET'),
              uri)
    client = httpclient.AsyncHTTPClient()
    headers = kwargs.setdefault("headers", {})
    headers.update({"X-XCAP-Asserted-Identity": user})
    kwargs['allow_ipv6'] = True
    client.fetch(uri,
                 callback,
                 **kwargs)

def get_simservs(user, callback):
    uri = simservs_uri(user)
    fetch_with_headers(user,
                       uri,
                       callback,
                       method="GET")

def put_simservs(user, xml_data, callback):
    uri = simservs_uri(user)
    fetch_with_headers(user,
                       uri,
                       callback,
                       method="PUT",
                       body=xml_data)

def delete_simservs(user, callback):
    uri = simservs_uri(user)
    fetch_with_headers(user,
                       uri,
                       callback,
                       method="DELETE")

