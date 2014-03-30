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
import httplib
import json

from tornado.web import HTTPError, asynchronous
from functools import partial

from metaswitch.ellis.api import _base
from metaswitch.ellis.api.utils import HTTPCallbackGroup
from metaswitch.ellis.data import numbers, users, NotFound
from metaswitch.ellis import settings
from metaswitch.ellis.remote import homestead
from metaswitch.ellis.remote import xdm
from metaswitch.common import utils
from metaswitch.common import ifcs

_log = logging.getLogger("ellis.api")

NUM_RETRIES = 2

class NumbersHandler(_base.LoggedInHandler):
    def __init__(self, application, request, **kwargs):
        super(NumbersHandler, self).__init__(application, request, **kwargs)
        self._request_group = None
        self.__response = None
        self.__failure_response = None
        self._numbers = None

    @asynchronous
    def get(self, username):
        """Retrieve list of phone numbers."""
        user_id = self.get_and_check_user_id(username)
        self._numbers = numbers.get_numbers(self.db_session(), user_id)
        if len(self._numbers) == 0:
            self.finish({"numbers": []})
            return

        for number in self._numbers:
            number["number_id"] = number["number_id"].hex
            number["sip_uri"] = number["number"]
            number["sip_username"] = utils.sip_uri_to_phone_number(number["number"])
            number["domain"] = utils.sip_uri_to_domain(number["number"])
            number["number"] = utils.sip_uri_to_phone_number(number["number"])
            number["formatted_number"] = utils.format_phone_number(number["number"])

            _request_group = HTTPCallbackGroup(partial(self._on_get_success, number["sip_uri"]), self._on_get_failure)
            # We only store the public identities in Ellis, and must query
            # Homestead for the associated private identities
            homestead.get_associated_privates(number["sip_uri"],
                                              _request_group.callback())

    def _on_get_success(self, public_id, responses):
        _log.debug("Successfully fetched associated private identities")
        for response in responses:
            try:
                # Body is of format {"public_id": "<public_id>",
                #                    "private_ids": ["<private_id_1>", "<private_id_2>"...]}
                parsed_body = json.loads(response.body)
                # We only support one private id per public id, so only pull out first in list
                private_id = parsed_body["private_ids"][0]
                for number in [n for n in self._numbers if n["sip_uri"] == public_id]:
                    number["private_id"] = private_id

            except (TypeError, KeyError) as e:
                _log.error("Could not parse response: %s", response.body)
                self.send_error(httplib.BAD_GATEWAY,
                                reason="Upstream request failed: could not parse private identity list")
                return

        for number in self._numbers:
            if "private_id" not in number:
                _log.debug("Not all numbers have private IDs associated, not sending response to the browser yet...")
                return

        self.finish({"numbers": self._numbers})

    def _on_get_failure(self, response):
        _log.warn("Failed to fetch private identities from homestead")
        self.forward_error(response)

    @asynchronous
    def post(self, username):
        """Allocate a phone number."""
        _log.debug("Number allocation API call (PSTN = %s)", self.get_argument('pstn', 'false'))
        user_id = self.get_and_check_user_id(username)
        db_sess = self.db_session()
        pstn = self.get_argument('pstn', 'false') == 'true'
        private_id = self.get_argument('private_id', None)
        try:
            number_id = numbers.allocate_number(db_sess, user_id, pstn)
            sip_uri = numbers.get_number(db_sess, number_id, user_id)
            self.sip_uri = sip_uri
            _log.debug("SIP URI %s", sip_uri)
            # FIXME We shouldn't commit until we know XDM/HS have succeeded but
            # if we hold the transaction open we can deadlock
            # * Request 1 comes in and allocates a number, kicks off requests
            #   to XDM/Homestead, has transaction open, returns thread to Tornado
            # * Request 2 comes in, allocates same number, can't lock it for
            #   update because Request 1 is holding it.  Blocks.
            # * Request 1 gets response but the thread is tied up
            # * Request 2 SQL transaction times out.
            # * Request 1 probably completes..
            db_sess.commit()
        except NotFound:
            # FIXME email operator to tell them we're out of numbers!
            _log.warning("No available numbers")
            raise HTTPError(httplib.SERVICE_UNAVAILABLE,
                            "No available numbers")

        # Work out the response we'll send if the upstream requests
        # are successful.
        number = utils.sip_uri_to_phone_number(sip_uri)
        pretty_number = utils.format_phone_number(number)
        self.__response = {"sip_uri": sip_uri,
                           "sip_username": number,
                           "number": number,
                           "pstn": pstn,
                           "formatted_number": pretty_number,
                           "number_id": number_id.hex}

        # Generate a random password and store it in Homestead.
        _log.debug("Populating other servers...")
        self._request_group = HTTPCallbackGroup(self._on_post_success,
                                                self._on_post_failure)

        public_callback = self._request_group.callback()

        if private_id == None:
            # No private id was provided, so we need to create a new
            # digest in Homestead
            private_id = utils.sip_public_id_to_private(sip_uri)
            sip_password = utils.generate_sip_password()
            homestead.create_private_id(private_id,
                                        utils.sip_uri_to_domain(sip_uri),
                                        sip_password,
                                        self._request_group.callback())
            self.__response["sip_password"] = sip_password

        # Associate the new public identity with the private identity in Homestead
        # and store the iFCs in homestead.
        homestead.create_public_id(private_id,
                                   sip_uri,
                                   ifcs.generate_ifcs(utils.sip_uri_to_domain(sip_uri)),
                                   public_callback)

        self.__response["private_id"] = private_id

        # Concurrently, store the default simservs in XDM.
        with open(settings.XDM_DEFAULT_SIMSERVS_FILE) as xml_file:
            default_xml = xml_file.read()
        xdm.put_simservs(sip_uri, default_xml, self._request_group.callback())

    def _on_post_success(self, responses):
        _log.debug("Successfully updated all the backends")
        self.finish(self.__response)

    def _on_post_failure(self, response):
        _log.warn("Failed to update all the backends")
        # Save off response so we can pass error through
        self.__failure_response = response
        # Try to back out the changes so we don't leave orphaned data.
        remove_public_id(self.db_session(), self.sip_uri,
                         self._on_backout_success, self._on_backout_failure)

    def _on_backout_success(self, responses):
        _log.warn("Backed out changes after failure")
        self.forward_error(self.__failure_response)

    def _on_backout_failure(self, responses):
        _log.warn("Failed to back out changes after failure")
        self.forward_error(self.__failure_response)

def remove_public_id(db_sess, sip_uri, on_success, on_failure):
    """
       Looks up the private id related to the sip_uri, and then the public ids
       related the retrieved private id. If there are multiple public ids, then
       only the sip_uri is is removed from Homestead, and the association to its
       private id is destroyed. If this is the only public id associated with the
       private id, then both the private and public ids are removed from Homestead
       along with their associations
    """
    def _on_get_privates_success(responses):
        _log.debug("Got related private ids")
        # Body is of format {"private_ids": ["<private_id_1>", "<private_id_2>"...]}
        parsed_body = json.loads(responses[0].body)
        # We only support one private id per public id, so only pull out first in list
        private_id = parsed_body["private_ids"][0]
        request_group2 = HTTPCallbackGroup(partial(_on_get_publics_success, private_id),
                                           on_failure)
        homestead.get_associated_publics(private_id, request_group2.callback())

    def _on_get_publics_success(private_id, responses):
        _log.debug("Got related public ids")
        parsed_body = json.loads(responses[0].body)
        public_ids = parsed_body["associated_public_ids"]
        if (utils.sip_public_id_to_private(sip_uri) == private_id and
            len(public_ids) > 1):
            # Do not permit deletion of an original public identity if others exist
            # otherwise another may claim the same private id from the pool
            _log.error("Failed to delete default public ID %s while other IDs are attached to the same private ID" % sip_uri);
            _log.error("Other public IDs are %s" % ", ".join(public_ids))
            on_failure(responses[0])
        else:
            # Only delete the digest if there is only a single private identity
            # associated with our sip_uri (i.e. this is the last public id)
            delete_digest = (len(public_ids) == 1)
            _delete_number(db_sess, sip_uri, private_id, delete_digest, on_success, on_failure)

    def _on_get_privates_failure(responses):
        # The number has no records in Homestead
        _log.debug("Failed to retrieve private IDs for a public ID")
        _log.debug("Returning %s to the pool" % sip_uri)
        numbers.remove_owner(db_sess, sip_uri)
        db_sess.commit()
        on_success({})

    request_group = HTTPCallbackGroup(_on_get_privates_success, _on_get_privates_failure)
    homestead.get_associated_privates(sip_uri, request_group.callback())

def _delete_number(db_sess, sip_uri, private_id, delete_digest, on_success, on_failure):
    """
       Deletes all information associated with a private/public identity
       pair, optionally deleting the digest associated with the private identity
    """
    numbers.remove_owner(db_sess, sip_uri)
    db_sess.commit()

    # Concurrently, delete data from Homestead and Homer
    request_group = HTTPCallbackGroup(on_success, on_failure)
    if delete_digest:
        homestead.delete_private_id(private_id, request_group.callback())
    homestead.delete_public_id(sip_uri, request_group.callback())
    xdm.delete_simservs(sip_uri, request_group.callback())

class NumberHandler(_base.LoggedInHandler):
    def __init__(self, application, request, **kwargs):
        super(NumberHandler, self).__init__(application, request, **kwargs)
        self.__password_response = None
        self.__ifc_response = None
        self.__xdm_response = None

    @asynchronous
    def delete(self, username, sip_uri):
        """Deletes a given SIP URI."""
        _log.info("Request to delete %s by %s", sip_uri, username)
        user_id = self.get_and_check_user_id(username)
        self.check_number_ownership(sip_uri, user_id)
        remove_public_id(self.db_session(), sip_uri, self._on_delete_success, self._on_delete_failure)

    def _on_delete_success(self, responses):
        _log.debug("All requests successful.")
        self.finish({})

    def _on_delete_failure(self, response):
        _log.debug("At least one request failed.")
        self.forward_error(response)


class SipPasswordHandler(_base.LoggedInHandler):
    @asynchronous
    def post(self, username, sip_uri):
        """Resets the password for the given SIP URI."""
        user_id = self.get_and_check_user_id(username)
        self.check_number_ownership(sip_uri, user_id)
        self.sip_digest_realm = utils.sip_uri_to_domain(sip_uri)
        self.sip_password = utils.generate_sip_password()

        # Fetch private ID from Homestead for this public ID
        self._request_group = HTTPCallbackGroup(self.on_get_privates_success,
                                                self.on_get_privates_failure)
        homestead.get_associated_privates(sip_uri, self._request_group.callback())

    def on_get_privates_success(self, responses):
        _log.debug("Got related private ids")
        # Body is of format {"public_id": "<public_id>",
        #                    "private_ids": ["<private_id_1>", "<private_id_2>"...]}
        parsed_body = json.loads(responses[0].body)
        # We only support one private id per public id, so only pull out first in list
        private_id = parsed_body["private_ids"][0]

        # Do not expect a response body, as long as there is no error, we are fine
        self._request_group = HTTPCallbackGroup(self.on_put_password_success,
                                                self.on_put_password_failure)
        homestead.put_password(private_id,
                               self.sip_digest_realm,
                               self.sip_password,
                               self._request_group.callback())

    def on_get_privates_failure(self, response):
        _log.error("Failed to get associated private ID from homestead %s", response)
        self.forward_error(response)

    def on_put_password_success(self, responses):
        self.finish({"sip_password": self.sip_password})

    def on_put_password_failure(self, response):
        _log.error("Failed to set password in homestead %s", response)
        self.forward_error(response)

class RemoteProxyHandler(_base.LoggedInHandler):
    def __init__(self, application, request, **kwargs):
        """
           Abstract handler that proxies requests to a remote server (e.g.
           Homer or Homestead)

           Subclasses should override self.remote_get and self.remote_put
           with relevant methods for contacting remotes
        """
        super(RemoteProxyHandler, self).__init__(application, request, **kwargs)
        # Using the request group approach as we may need to pull/push multiple docs
        # in the future
        self._request_group = None
        self.__response = None
        self.remote_name = None
        self.remote_get = None
        self.remote_put = None

    @asynchronous
    def get(self, username, sip_uri):
        """Fetches document from remote"""
        user_id = self.get_and_check_user_id(username)
        self.check_number_ownership(sip_uri, user_id)

        self._request_group = HTTPCallbackGroup(self._on_get_success,
                                                self._on_get_failure)
        self.remote_get(sip_uri, self._request_group.callback())

    def _on_get_success(self, responses):
        _log.debug("Successfully fetched from %s" % self.remote_name)
        self.finish(responses[0].body)

    def _on_get_failure(self, response):
        _log.warn("Failed to fetch from %s" % self.remote_name)
        self.forward_error(response)

    @asynchronous
    def put(self, username, sip_uri):
        """Updates document on remote"""
        user_id = self.get_and_check_user_id(username)
        self.check_number_ownership(sip_uri, user_id)
        response_body = self.request.body
        self._request_group = HTTPCallbackGroup(self._on_put_success,
                                                self._on_put_failure)
        self.remote_put(sip_uri, response_body, self._request_group.callback())

    def _on_put_success(self, responses):
        _log.debug("Successfully updated %s" % self.remote_name)
        self.finish(self.__response)

    def _on_put_failure(self, response):
        _log.warn("Failed to update %s" % self.remote_name)
        self.forward_error(response)

class SimservsHandler(RemoteProxyHandler):
    def __init__(self, application, request, **kwargs):
        super(SimservsHandler, self).__init__(application, request, **kwargs)
        """Updates the simservs on the XDM"""
        self.remote_get = xdm.get_simservs
        self.remote_put = xdm.put_simservs
        self.remote_name = "Homer (simservs)"

class IFCsHandler(RemoteProxyHandler):
    def __init__(self, application, request, **kwargs):
        """Updates the iFCs on Homestead"""
        super(IFCsHandler, self).__init__(application, request, **kwargs)
        self.remote_get = homestead.get_filter_criteria
        self.remote_put = homestead.put_filter_criteria
        self.remote_name = "Homestead (iFC)"

class NumberGabListedHandler(_base.LoggedInHandler):
    def get(self, username, sip_uri):
        """Retrieves GAB listed setting for a given phone number"""
        user_id = self.get_and_check_user_id(username)
        db_sess = self.db_session()
        try:
            gab_listed = numbers.is_gab_listed(db_sess, user_id, sip_uri)
        except NotFound:
            _log.warning("Could not retrieve gab listing")
            raise HTTPError(httplib.NOT_FOUND)

        self.finish({"gab_listed": gab_listed})

    def put(self, username, sip_phone, isListed):
        """Updates GAB listed setting for a given phone number"""
        user_id = self.get_and_check_user_id(username)
        db_sess = self.db_session()
        number_id = numbers.get_sip_uri_number_id(db_sess, sip_phone)
        numbers.update_gab_list(db_sess, user_id, number_id, isListed)
        db_sess.commit()
        self.finish({})

class GabListedNumbersHandler(_base.LoggedInHandler):
    def get(self):
        """List of numbers that are available for users to contact"""
        db_sess = self.db_session()
        contact_list = numbers.get_listed_numbers(db_sess)
        self.finish({"contacts": contact_list})
