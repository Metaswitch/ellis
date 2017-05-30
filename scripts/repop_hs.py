#!/usr/bin/env python

# @file repop_hs.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import sys
from tornado import ioloop

from metaswitch.ellis.data import connection
from metaswitch.ellis.remote import homestead
from metaswitch.ellis import settings

from metaswitch.common import utils
from metaswitch.common import ifcs

num_requests = 0
num_responses = 0
errors = 0

def standalone():
    global num_responses, num_requests

    db_sess = connection.Session()
    c = db_sess.execute("SELECT number FROM numbers where OWNER_ID is not NULL;")

    def inc_resp_count():
        global num_responses, num_requests
        num_responses += 1
        print "%s responses outstanding" % (num_requests - num_responses)
        if num_responses == num_requests:
            print "Last response"
            print "There were %d errors" % errors
            io_loop.stop()

    for (sip_uri,) in c:
        print "%s Sending request" % (sip_uri,)

        def get_ifc_callback(response, sip_uri=sip_uri):
            """
            Handle response to initial GET, only PUT new data if there 
            wasn't anything there.
            """
            global num_responses, num_requests
            print "%s Get ifc response %s" % (sip_uri, response.code)
            if response.code == 404:
                print "%s ifc needs to be repopulated" % (sip_uri,)
                homestead.put_filter_criteria(sip_uri, ifcs.generate_ifcs(utils.sip_uri_to_domain(sip_uri)), put_ifc_callback)
            else:
                inc_resp_count()

        def put_ifc_callback(response, sip_uri=sip_uri):
            """
            Handle put response, report errors, issue a final GET to 
            check we succeeded.
            """
            global num_responses, num_requests, errors
            print "%s Put ifc response %s" % (sip_uri, response.code)
            if response.code // 100 != 2:
                print >> sys.stderr, "%s Bad response %s" % (sip_uri, response)
                errors += 1
            homestead.get_filter_criteria(sip_uri, check_callback)

        def get_digest_callback(response, sip_uri=sip_uri):
            """
            Handle response to initial GET, only PUT new data if there 
            wasn't anything there.
            """
            global num_responses, num_requests
            print "%s Get digest response %s" % (sip_uri, response.code)
            if response.code == 404:
                print "%s digest needs to be repopulated" % (sip_uri,)
                homestead.put_password(sip_uri, sip_uri, utils.generate_sip_password(), post_digest_callback)
            else:
                inc_resp_count()

        def post_digest_callback(response, sip_uri=sip_uri):
            """
            Handle post response, report errors, issue a final GET to 
            check we succeeded.
            """
            global num_responses, num_requests, errors
            print "%s Post digest response %s" % (sip_uri, response.code)
            if response.code // 100 != 2:
                print >> sys.stderr, "%s Bad response %s" % (sip_uri, response)
                errors += 1
            homestead.get_digest(sip_uri, check_callback)

        def check_callback(response, sip_uri=sip_uri):
            """
            Handle response to the check request, reports errors.
            """
            global num_responses, num_requests, errors
            print "%s Check response %s" % (sip_uri, response.code)
            if response.code != 200:
                print >> sys.stderr, "%s Bad response %s" % (sip_uri, response)
                errors += 1
            inc_resp_count()

        num_requests += 2
        homestead.get_digest(sip_uri, get_digest_callback)
        homestead.get_filter_criteria(sip_uri, get_ifc_callback)
    print "Finished queuing requests."


if __name__ == '__main__':
    connection.init_connection()
    io_loop = ioloop.IOLoop.instance()
    io_loop.add_callback(standalone)
    io_loop.start()
