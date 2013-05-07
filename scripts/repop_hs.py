#!/usr/bin/env python

# @file repop_hs.py
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


import sys
from tornado import ioloop

from metaswitch.ellis.data import connection
from metaswitch.ellis.remote import homestead
from metaswitch.ellis import settings

from metaswitch.common import utils
from metaswitch.common import ifcs

def get_digest(user, callback):
    url = homestead.digest_url(user, user)
    homestead.fetch(url, callback, method="GET")

def get_filter_criteria(user, callback):
    url = homestead.filter_url(user)
    homestead.fetch(url, callback, method="GET")

num_requests = 0
num_responses = 0
errors = 0

def standalone():
    global num_responses, num_requests

    db_sess = connection.Session()
    c = db_sess.execute("SELECT number FROM numbers;")

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
                homestead.put_filter_criteria(sip_uri, ifcs.generate_ifcs(settings.SIP_DIGEST_REALM), put_ifc_callback)
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
            get_filter_criteria(sip_uri, check_callback)

        def get_digest_callback(response, sip_uri=sip_uri):
            """
            Handle response to initial GET, only PUT new data if there 
            wasn't anything there.
            """
            global num_responses, num_requests
            print "%s Get digest response %s" % (sip_uri, response.code)
            if response.code == 404:
                print "%s digest needs to be repopulated" % (sip_uri,)
                homestead.post_password(sip_uri, sip_uri, utils.generate_sip_password(), post_digest_callback)
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
            get_digest(sip_uri, check_callback)

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
        get_digest(sip_uri, get_digest_callback)
        get_filter_criteria(sip_uri, get_ifc_callback)
    print "Finished queuing requests."


if __name__ == '__main__':
    connection.init_connection()
    io_loop = ioloop.IOLoop.instance()
    io_loop.add_callback(standalone)
    io_loop.start()
