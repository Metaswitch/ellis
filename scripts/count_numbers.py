#!/usr/bin/env python

# @file count_numbers.py
#
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by post at
# Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK


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
