#!/usr/bin/env python

# @file sync_databases.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import logging
import json

from optparse import OptionParser

from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient

from metaswitch.common import ifcs, utils, logging_config
from metaswitch.ellis.data import numbers, connection
from metaswitch.ellis.remote import homestead, xdm
from metaswitch.ellis import settings

_log = logging.getLogger("ellis.create_numbers")

AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient",
                          max_clients=100)
connection.init_connection()
db_session = connection.Session()

pending_requests = 0
inconsistent_uris = set()
stats = {"Assigned numbers in Ellis": 0,
         "Unassigned numbers in Ellis": 0,
         "Credentials & associations deleted": 0,
         "Simservs & iFCs deleted": 0,
         "Missing IFCs re-created": 0,
         "Errors": 0}

def create_get_handler(sip_uri, on_found=None, on_not_found=None):
    """
    Handler that asserts that a resource exists, executing the on_not_found handler if not
    """
    def handle_get(response):
        global pending_requests
        url = response.request.url
        if not response.error:
            print "Successful GET from %s" % url
            if on_found:
                data = json.loads(response.body)
                on_found(sip_uri, **data)
        elif response.code == 404:
            print "404 for %s" % url
            if on_not_found:
                on_not_found()
        else:
            print "Error %s while GET %s" % (response.error, url)
            stats["Errors"] += 1
        pending_requests -= 1
        if pending_requests == 0:
            on_complete()
    return handle_get

def logging_handler(response):
    """
    Handler for requests where we only want to log out the result
    """
    global pending_requests
    url = response.request.url
    method = response.request.method
    if not response.error:
        print "Successful %s from %s" % (method, url)
    else:
        print "Error %s while %s %s" % (response.error, method, url)
        stats["Errors"] += 1
    pending_requests -= 1
    if pending_requests == 0:
        on_complete()

def validate_line(sip_uri):
    """
    Validate details about line in homestead
    """
    print "Validating %s " % sip_uri
    # Verify the private id exists for this line exists in homestead, delete the line otherwise
    global pending_requests
    pending_requests += 1
    delete_line = number_deleter(None, sip_uri)
    homestead.get_associated_privates(sip_uri,
                                      create_get_handler(sip_uri,
                                                         on_found=ensure_digest_exists,
                                                         on_not_found=delete_line))

def invalidate_line(sip_uri):
    """
    Try to get private id and then delete all details from Homestead
    """
    print "Invalidating %s " % sip_uri
    # Verify the private id exists for this line exists in homestead, delete the line otherwise
    global pending_requests
    pending_requests += 1
    delete_line = number_deleter(None, sip_uri)

    def extract_private_and_delete(sip_uri, **kwargs):
        private_id = kwargs["private_ids"][0]
        delete_line_with_private = number_deleter(private_id, sip_uri)
        delete_line_with_private()

    homestead.get_associated_privates(sip_uri,
                                      create_get_handler(sip_uri,
                                                         on_found=extract_private_and_delete,
                                                         on_not_found=delete_line))

def number_deleter(private_id, sip_uri):
    def delete_line():
        """
        Remove details about line from ellis, homestead and homer
        """
        print "Deleting %s %s" % (private_id, sip_uri)
        numbers.remove_owner(db_session, sip_uri)
        # Attempt to delete info about line from remotes
        global pending_requests
        if private_id:
            stats["Credentials & associations deleted"] += 1
            pending_requests += 2
            homestead.delete_password(private_id, logging_handler)
            homestead.delete_associated_public(private_id, sip_uri, logging_handler)
        stats["Simservs & iFCs deleted"] += 1
        pending_requests += 2
        homestead.delete_filter_criteria(sip_uri, logging_handler)
        xdm.delete_simservs(sip_uri, logging_handler)

    return delete_line

def ensure_digest_exists(sip_uri, **kwargs):
    private_id = kwargs["private_ids"][0]
    print "Verifying digest exists for %s" % private_id
    global pending_requests
    pending_requests+=1
    delete_line = number_deleter(private_id, sip_uri)
    homestead.get_digest(private_id,
                         create_get_handler(sip_uri,
                                            on_found=ensure_valid_ifc,
                                            on_not_found=delete_line))

def ensure_valid_ifc(sip_uri, **kwargs):
    """
    Check if a line has valid IFC, populate with default if not
    """
    print "Verifying IFC for %s" % sip_uri
    global pending_requests
    pending_requests+=1
    def put_default_ifc():
        print "Adding default IFC for %s" % sip_uri
        stats["Missing IFCs re-created"] += 1
        global pending_requests
        pending_requests+=1
        homestead.put_filter_criteria(sip_uri,
                                      ifcs.generate_ifcs(utils.sip_uri_to_domain(sip_uri)),
                                      logging_handler)
    homestead.get_filter_criteria(sip_uri,
                                  create_get_handler(sip_uri, on_not_found=put_default_ifc))
def check_existing_uris():
    """
    Get list of numbers that ellis thinks exist and:
    - Verify the digest exists in homestead, deleting the line if not.
    - If the digest exists, but the IFC does not, put in the default IFC
    """
    cursor = db_session.execute("SELECT number FROM numbers WHERE owner_id IS NOT NULL")
    assigned_numbers = [row[0] for row in cursor.fetchall()]
    stats["Assigned numbers in Ellis"] = len(assigned_numbers)
    for sip_uri in assigned_numbers:
        validate_line(sip_uri)

def remove_nonexisting_uris():
    """
    Get list of numbers that ellis thinks do not exist and
    remove any record of them from homestead and homer
    """
    cursor = db_session.execute("SELECT number FROM numbers WHERE owner_id IS NULL")
    unassigned_numbers = [row[0] for row in cursor.fetchall()]
    stats["Unassigned numbers in Ellis"] = len(unassigned_numbers)
    for sip_uri in unassigned_numbers:
        invalidate_line(sip_uri)

def on_complete():
    """
    Called when all request have completed
    """
    IOLoop.instance().stop()
    db_session.commit()
    # To avoid counting the lines deleted as part of the unassigned, subtract these
    # from the line delete count
    stats["Simservs & iFCs deleted"] -= stats["Unassigned numbers in Ellis"]
    print "\nSummary:"
    table_format = "{:<40}{}"
    for s in stats:
        print table_format.format(s, stats[s])

def standalone():
    """
    Entry point to script
    """
    check_existing_uris()
    remove_nonexisting_uris()
    IOLoop.instance().start()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--log-level",
                      dest="log_level",
                      default=2,
                      type="int")
    (options, args) = parser.parse_args()

    if args:
        parser.print_help()
    else:
        logging_config.configure_logging(
                utils.map_clearwater_log_level(options.log_level),
                settings.LOGS_DIR,
                settings.LOG_FILE_PREFIX,
                "sync_databases")

        standalone()
