#!/usr/bin/env python

# @file utils.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015  Metaswitch Networks Ltd
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


import sys
import re
import json
import logging
import tornado.ioloop
from tornado.web import HTTPError
import xml.dom.minidom;
from metaswitch.ellis import settings
from metaswitch.ellis.remote import homestead

_log = logging.getLogger();

def setup_logging(level=logging.ERROR):
    """
    Sets up logging so that the specified level is sent to stdout.
    """
    # Create a StreamHandler to send logs to stdout.
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(level)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    stdout.setFormatter(formatter)

    # Hang it off the root logger.
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(stdout)

def parse_dn_ranges(dn_ranges):
    """
    A generator that parses DN ranges of the form <start-dn>..<end-dn>,... or
    <single-dn>,... and yields each individual DN.
    """
    for dn_range in dn_ranges.split(","):
        # Split on .. into start and end DNs.  If there's no .., set them identically.
        dn_range = dn_range.split("..")
        start_dn = dn_range[0]
        end_dn = dn_range[1] if len(dn_range) > 1 else dn_range[0]

        if len(start_dn) != len(end_dn):
            _log.error("Directory number range %s..%s has different start and end number lengths", start_dn, end_dn)
            continue

        # Find any non-numeric prefix (e.g. +) and check that both numbers have it.
        dn_prefix = re.search("$[^0-9]*", start_dn).group(0)
        if not end_dn.startswith(dn_prefix):
            _log.error("Directory number range %s..%s has different start and end number prefixes", start_dn, end_dn)
            continue

        # Strip the prefix, iterate through the resulting numbers and yield them
        start_num = int(start_dn[len(dn_prefix):])
        end_num = int(end_dn[len(dn_prefix):])
        for num in range(start_num, end_num + 1):
            yield "%s%d" % (dn_prefix, num)

def build_ifc(ifc_file, domain, twin_prefix):
    """
    Loads IFC from disk (defaulting if not supplied) and then fills in any
    ${DOMAIN} or ${PREFIX} placeholders in it.
    """
    if ifc_file:
        try:
            with open(ifc_file, 'r') as f:
                ifc = f.read()
                return None
        except IOError as e:
            _log.error("Failed to read %s - %s", ifc_file, e.strerror)
    else:
        ifc=('<?xml version="1.0" ?>\n'
              '<ServiceProfile>\n'
              '</ServiceProfile>')

    ifc = ifc.replace("${DOMAIN}", domain)
    ifc = ifc.replace("${PREFIX}", twin_prefix)

    return ifc

class Callback:
    args = None

    def __call__(self, *args):
        self.args = args
        tornado.ioloop.IOLoop.instance().stop()

    def wait(self):
        tornado.ioloop.IOLoop.instance().start()
        return self.args

def check_connection():
    callback = Callback()

    homestead.ping(callback)
    response = callback.wait()[0]
    if response.body != "OK":
        _log.error("Can't contact homestead-prov at http://%s", settings.HOMESTEAD_URL)
        return False
    return True

def create_user(private_id, public_id, domain, password, ifc, plaintext=False):
    callback = Callback()

    homestead.get_digest(private_id, callback)
    response = callback.wait()[0]
    if isinstance(response, HTTPError) and response.code != 404:
        _log.error("Failed to check private ID %s - HTTP status code %d", private_id, response.code)
        return False
    if response.code == 200:
        _log.error("Private ID %s already exists - not creating", private_id)
        return True

    homestead.create_private_id(private_id, domain, password, callback, plaintext=plaintext)
    response = callback.wait()[0]
    if isinstance(response, HTTPError):
        _log.error("Failed to create private ID %s - HTTP status code %d", private_id, response.code)
        return False

    homestead.create_public_id(private_id, public_id, ifc, callback)
    response = callback.wait()[0]
    if isinstance(response, HTTPError):
        _log.error("Failed to create public ID %s - HTTP status code %d", public_id, response.code)
        return False

    return True

def update_user(private_id, public_id, domain, password, ifc, plaintext=False):
    callback = Callback()

    if password:
        homestead.put_password(private_id, domain, password, callback, plaintext=plaintext)
        response = callback.wait()[0]
        if isinstance(response, HTTPError):
            _log.error("Failed to update password for private ID %s - HTTP status code %d", private_id, response.code)
            return False

    if ifc:
        homestead.put_filter_criteria(public_id, ifc, callback)
        response = callback.wait()[0]
        if isinstance(response, HTTPError):
            _log.error("Failed to update public ID %s - HTTP status code %d", public_id, response.code)
            return False

    return True

def delete_user(private_id, public_id, force=False):
    success = True
    callback = Callback()

    homestead.delete_public_id(public_id, callback)
    response = callback.wait()[0]
    if isinstance(response, HTTPError):
        _log.error("Failed to delete public ID %s - HTTP status code %d", private_id, response.code)
        success = False
        if not force:
            return success

    homestead.delete_private_id(private_id, callback)
    response = callback.wait()[0]
    if isinstance(response, HTTPError):
        _log.error("Failed to delete private ID %s - HTTP status code %d", private_id, response.code)
        success = False

    return success

def display_user(private_id, public_id, short=False):
    success = True
    callback = Callback()

    if not short:
        print "%s:" % (private_id,)

    homestead.get_digest(private_id, callback)
    response = callback.wait()[0]
    if response.code == 200:
        av = json.loads(response.body)
        if 'digest_ha1' in av:
            password = av['digest_ha1']
            if 'plaintext_password' in av:
                password += " (%s)" % (av['plaintext_password'],)
            if short:
                print "%s:%s" % (private_id, password)
            else:
                print "  HA1 digest:"
                print "    %s" % (password,)
    else:
        _log.error("Failed to retrieve digest for private ID %s - HTTP status code %d", private_id, response.code)
        success = False

    if not short:
        homestead.get_filter_criteria(public_id, callback)
        response = callback.wait()[0]
        if response.code == 200:
            ifc = xml.dom.minidom.parseString(response.body)
            ifc_str = ifc.toprettyxml(indent="  ")
            ifc_str = "\n".join(filter(lambda l: l.strip() != "", ifc_str.split("\n")))
            ifc_str = "    " + ifc_str.replace("\n", "\n    ")
            print "  iFC:"
            print ifc_str
        else:
            _log.error("Failed to retrieve iFC for public ID %s - HTTP status code %d", public_id, response.code)
            success = False

    return success
