#!/usr/bin/env python

# @file repop_xdm.py
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
from metaswitch.ellis.remote import xdm
from metaswitch.ellis import settings
from metaswitch.common.simservs import default_simservs

def get_simservs(user, callback):
    uri = xdm.simservs_uri(user)
    xdm.fetch_with_headers(user,
                           uri,
                           callback,
                           method="GET")

num_requests = 0
num_responses = 0
errors = 0

def standalone():
    global num_responses, num_requests
    xml = default_simservs()
    print "XML: %s" % xml

    db_sess = connection.Session()
    c = db_sess.execute("SELECT number FROM numbers WHERE owner_id IS NOT NULL;")

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

        def get_callback(response, sip_uri=sip_uri):
            """
            Handle response to initial GET, only PUT new data if there
            wasn't anything there.
            """
            global num_responses, num_requests
            print "%s Get response %s" % (sip_uri, response.code)
            if response.code == 404:
                print "%s needs to be repopulated" % (sip_uri,)
                xdm.put_simservs(sip_uri, xml, put_callback)
            else:
                inc_resp_count()

        def put_callback(response, sip_uri=sip_uri):
            """
            Handle put response, report errors, issue a final GET to
            check we succeeded.
            """
            global num_responses, num_requests, errors
            print "%s Put response %s" % (sip_uri, response.code)
            if response.code // 100 != 2:
                print >> sys.stderr, "%s Bad response %s" % (sip_uri, response)
                errors += 1
            get_simservs(sip_uri, check_callback)

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

        num_requests += 1
        get_simservs(sip_uri, get_callback)
    print "Finished queuing requests."


if __name__ == '__main__':
    connection.init_connection()
    io_loop = ioloop.IOLoop.instance()
    io_loop.add_callback(standalone)
    io_loop.start()
