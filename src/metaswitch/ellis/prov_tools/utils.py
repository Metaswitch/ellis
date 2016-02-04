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
        dn_prefix = re.search("^[^0-9]*", start_dn).group(0)
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
        except IOError as e:
            _log.error("Failed to read %s - %s", ifc_file, e.strerror)
            return None
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

def conditional_print(condition, text):
    if condition:
        print text

# quiet flag will prevent any output to stdout. This way we can check that the
# user exists and has valid xml, without swamping the output with large iFCs
def display_user(public_id, short=False, quiet=False):
    success = True
    callback = Callback()

    if not short:
        conditional_print(not quiet, "Public User ID %s:" % (public_id))

    homestead.get_associated_privates(public_id, callback)
    response = callback.wait()[0]
    public_id_missing = (response.code == 404)
    if response.code == 200:
        private_ids = json.loads(response.body)
        for private_id in private_ids['private_ids']:
            homestead.get_digest(private_id, callback)
            response = callback.wait()[0]
            if response.code == 200:
                av = json.loads(response.body)
                if 'digest_ha1' in av:
                    password = av['digest_ha1']
                    if 'plaintext_password' in av:
                        password += " (%s)" % (av['plaintext_password'],)
                    if short:
                        conditional_print(not quiet, "%s/%s: %s" % (public_id, private_id, password))
                    else:
                        conditional_print(not quiet, "  Private User ID %s:" % (private_id,))
                        conditional_print(not quiet, "    HA1 digest: %s" % (password,))
            else:
                _log.error("Failed to retrieve digest for private ID %s - HTTP status code %d", private_id, response.code)
                success = False
    else:
        _log.error("Failed to retrieve private IDs for public ID %s - HTTP status code %d", public_id, response.code)
        success = False

    # Default to True so that if we don't check, we may still report that no
    # information was found.
    filter_criteria_missing = True
    if not short:
        homestead.get_filter_criteria(public_id, callback)
        response = callback.wait()[0]
        filter_criteria_missing = (response.code == 404)
        if response.code == 200:
            ifc = xml.dom.minidom.parseString(response.body)
            ifc_str = ifc.toprettyxml(indent="  ")
            ifc_str = "\n".join(filter(lambda l: l.strip() != "", ifc_str.split("\n")))
            ifc_str = "    " + ifc_str.replace("\n", "\n    ")

            conditional_print(not quiet, "  iFC:")
            conditional_print(not quiet, ifc_str)
        else:
            _log.error("Failed to retrieve iFC for public ID %s - HTTP status code %d", public_id, response.code)
            success = False

    if filter_criteria_missing and public_id_missing:
        _log.error("Failed to find any information for public ID %s.", public_id)

    return success


def list_users(target_users_per_chunk=100, keep_going=False):
    """
    A generator that lists users.  Rather than querying all users from the homestead-prov server
    in one huge request (which would impact its performance), it tunes itself to query
    approximately the specified number of users per chunk.  It does this by starting off with a
    small chunk size and scaling up/down according to the number of users it receives.  All chunk
    sizes are always powers of 2.
    """
    MAX_CHUNK_PROPORTION = 2**24
    chunk_proportion = MAX_CHUNK_PROPORTION
    chunk = 0
    exception = StopIteration
    while chunk < chunk_proportion:
        try:
            _log.debug("Bulk-retrieving public IDs (chunk %d/%d)\n", chunk, chunk_proportion)
            public_ids = get_users(chunk, chunk_proportion)
            _log.debug("Retrieved %d public IDs\n", len(public_ids))
            for public_id in (public_id_obj['public_id'] for public_id_obj in public_ids):
                yield public_id

            # Move onto the next chunk and then decide whether we should change chunk size.
            chunk += 1
            if len(public_ids) < target_users_per_chunk * 0.5 and chunk % 2 == 0:
                _log.debug("Too few public IDs in chunk - increase chunk size")
                chunk /= 2
                chunk_proportion /= 2
            elif len(public_ids) > target_users_per_chunk * 2 and chunk_proportion * 2 <= MAX_CHUNK_PROPORTION:
                _log.debug("Too many public IDs in chunk - reduce chunk size")
                chunk *= 2
                chunk_proportion *= 2

        except HTTPError as e:
            # We caught an error.  We should rethrow it, but maybe defer that for now.
            exception = e
            if not keep_going:
                break
    raise exception


def get_users(chunk, chunk_proportion, full=False):
    callback = Callback()

    homestead.get_public_ids(chunk, chunk_proportion, True, callback)
    response = callback.wait()[0]
    if response.error:
        _log.error("Failed to bulk retrieve public IDs (chunk %d/%d) - HTTP status code %d", chunk, chunk_proportion, response.code)
        raise response.error

    chunk_rsp = json.loads(response.body)
    return chunk_rsp['public_ids']
