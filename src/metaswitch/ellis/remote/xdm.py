# @file xdm.py
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

from tornado import httpclient

from metaswitch.ellis import settings

_log = logging.getLogger("ellis.remote")

def simservs_uri(user):
    encoded_user = urllib.quote(user, safe="")
    path = "org.etsi.ngn.simservs/users/%s/simservs.xml" % encoded_user
    uri = "http://%s/%s" % (settings.XDM_URL, path)
    return uri

def fetch_with_headers(user, uri, callback, **kwargs):
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

