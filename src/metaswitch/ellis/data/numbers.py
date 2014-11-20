# @file numbers.py
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
import uuid

from metaswitch.ellis.data._base import NotFound

_log = logging.getLogger("ellis.data")

def get_numbers(db_sess, user_id):
    cursor = db_sess.execute("""
                             SELECT number_id, number, pstn, gab_listed FROM numbers
                             WHERE owner_id = :user
                             ORDER BY pstn DESC, number
                             """, {"user": user_id})

    return [{"number_id": uuid.UUID(row[0]),
             "number": row[1],
             "pstn": row[2],
             "gab_listed": row[3]} for row in cursor.fetchall()]

def get_sip_uri_owner_id(db_sess, sip_uri):
    cursor = db_sess.execute("""
                             SELECT owner_id FROM numbers
                             WHERE number = :number
                             """, {"number": sip_uri})

    try:
        owner_id = cursor.fetchone()[0]
        if owner_id is None:
            _log.info("Null owner ID for %s", sip_uri)
            raise NotFound()
        return owner_id
    except TypeError:
        _log.info("Not found: %s", sip_uri)
        raise NotFound()

def get_sip_uri_number_id(db_sess, sip_uri):
    cursor = db_sess.execute("""
                             SELECT number_id FROM numbers
                             WHERE number = :number
                             """, {"number": sip_uri})

    try:
        number_id = cursor.fetchone()[0]
        if number_id is None:
            _log.info("Null number ID for %s", sip_uri)
            raise NotFound()
        return number_id
    except TypeError:
        _log.info("Not found: %s", sip_uri)
        raise NotFound()

def remove_owner(db_sess, sip_uri):
    _log.debug("Removing owner of %s", sip_uri)
    number_id = get_sip_uri_number_id(db_sess, sip_uri)

    # Delete the number from the pool if it was allocated specifically,
    # rather than releasing it.
    db_sess.execute("""
                    DELETE from numbers
                    WHERE number_id = :number_id
                    AND allocated = TRUE
                    """, {"number_id": number_id})
    db_sess.execute("""
                    UPDATE numbers
                    SET owner_id = NULL
                    WHERE number_id = :number_id
                    """, {"number_id": number_id})

def add_number_to_pool(db_sess, number, pstn=False, allocated=False):
    _log.debug("Adding %s to the pool", number)
    number_id = uuid.uuid4()

    db_sess.execute("""
                   INSERT INTO numbers (number_id, number, pstn, allocated)
                   VALUES (:number_id, :number, :pstn, :allocated);
                   """,
                   {"number_id": number_id,
                    "number": number,
                    "pstn": pstn,
                    "allocated": allocated})

    _log.debug("Added %s to the pool", number)
    return number_id

def allocate_number(db_sess, user_id, pstn = False):
    # Randomize the number allocated.  ORDER BY RAND() is not the fastest way of
    # doing this, but it's fast enough and Ellis is only intended as a demo
    # tool anyway.
    if (pstn):
        _log.debug("Allocating a PSTN number")
        sql_query = """
                    SELECT number_id FROM numbers
                    WHERE owner_id IS NULL
                    AND pstn
                    ORDER BY RAND()
                    LIMIT 1;
                    """
    else:
        _log.debug("Allocating a non-PSTN number")
        sql_query = """
                    SELECT number_id FROM numbers
                    WHERE owner_id IS NULL
                    AND NOT pstn
                    ORDER BY RAND()
                    LIMIT 1;
                    """

    cursor = db_sess.execute(sql_query)
    available_number = cursor.fetchone()

    if available_number:
        (number_id,) = available_number
        _log.debug("Fetched %s", number_id)
        allocate_specific_number(db_sess, user_id, number_id)
        return uuid.UUID(number_id)

    raise NotFound()

def allocate_specific_number(db_sess, user_id, number_id):
        db_sess.execute("""
                        UPDATE numbers SET owner_id = :owner, gab_listed = 1
                        WHERE number_id = :number_id;
                        """, {"owner": user_id,
                              "number_id": number_id})
        _log.debug("Updated the owner")



def get_number(db_sess, number_id, expected_user_id):
    cursor = db_sess.execute("""
                             SELECT number, owner_id FROM numbers
                             WHERE number_id = :number_id;
                             """, {"number_id": number_id})
    try:
        number, user_id = cursor.fetchone()
        if user_id != expected_user_id:
            _log.warning("Number's user_id %s didn't match %s", user_id, expected_user_id)
            raise NotFound()
        return number
    except TypeError:
        raise NotFound()

def is_gab_listed(db_sess, expected_user_id, sip_uri):
    cursor = db_sess.execute("""
                             SELECT gab_listed FROM numbers
                             WHERE number = :sip_uri
                             AND owner_id = :owner_id;
                             """, {"sip_uri": sip_uri,
                                   "owner_id": expected_user_id})
    try:
        gab_listed = cursor.fetchone()[0]
        return gab_listed
    except TypeError:
        raise NotFound()


def update_gab_list(db_sess, user_id, number_id, isListed):
    db_sess.execute("""
                    UPDATE numbers SET gab_listed = :gab
                    WHERE number_id = :nid
                    """,
                    {"gab": isListed, "nid": number_id})


def get_listed_numbers(db_sess):
    cursor = db_sess.execute("""
                              SELECT u.user_id, u.full_name, u.email, n.number, n.pstn
                              FROM numbers n
                              INNER JOIN users u ON u.user_id = n.owner_id
                              WHERE n.gab_listed = 1
                              ORDER BY u.full_name, n.pstn DESC, n.number
                             """)

    last_user_id = None
    current_output_row = None
    output = []

    # TODO Return the PSTN flag with the numbers, requires change to GAB JSON API.
    for user_id, full_name, email, number, pstn in cursor:
        if last_user_id != user_id:
            # We're looking at a new user
            current_output_row = {"full_name": full_name,
                                  "email": email,
                                  "numbers": [number]}
            output.append(current_output_row)
            last_user_id = user_id
        else:
            current_output_row["numbers"].append(number)

    return output
