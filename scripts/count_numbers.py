#!/usr/bin/env python

# @file count_numbers.py
#
# Copyright (C) Metaswitch Networks 2013
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


from metaswitch.ellis.data import connection

def standalone():
    db_sess = connection.Session()
    c = db_sess.execute("SELECT count(*) FROM numbers WHERE NOT pstn AND owner_id IS NULL;")
    non_pstn_avail_count = c.fetchone()[0]
    c = db_sess.execute("SELECT count(*) FROM numbers WHERE NOT pstn;")
    non_pstn_total_count = c.fetchone()[0]
    c = db_sess.execute("SELECT count(*) FROM numbers WHERE pstn AND owner_id IS NULL;")
    pstn_avail_count = c.fetchone()[0]
    c = db_sess.execute("SELECT count(*) FROM numbers WHERE pstn;")
    pstn_total_count = c.fetchone()[0]

    print "Available non-PSTN numbers %s" % non_pstn_avail_count
    print "Taken non-PSTN numbers %s" % (non_pstn_total_count - non_pstn_avail_count)
    print "Total non-PSTN numbers %s" % non_pstn_total_count
    print ""
    print "Available PSTN numbers %s" % pstn_avail_count
    print "Taken PSTN numbers %s" % (pstn_total_count - pstn_avail_count)
    print "Total PSTN numbers %s" % pstn_total_count

if __name__ == '__main__':
    connection.init_connection()
    standalone()
