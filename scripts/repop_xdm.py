#!/usr/bin/env python

# @file repop_xdm.py
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
from metaswitch.ellis.remote import xdm
from metaswitch.ellis import settings

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
    with open(settings.XDM_DEFAULT_SIMSERVS_FILE, "rb") as xml_file:
        xml = xml_file.read()
    print "XML: %s" % xml

    db_sess = connection.Session()
    c = db_sess.execute("SELECT number FROM numbers WHERE owner_id IS NULL;")

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
