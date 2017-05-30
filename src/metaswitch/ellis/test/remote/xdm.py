#!/usr/bin/python

# @file xdm.py
#
# Copyright (C) Metaswitch Networks 2014
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import unittest
from mock import patch, Mock

from metaswitch.ellis.remote import xdm

SIP_URI = "sip:1234@foo.com"
XML = """<?xml version="1.0" encoding="UTF-8"?>
<simservs xmlns="http://uri.etsi.org/ngn/params/xml/simservs/xcap" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
  <originating-identity-presentation active="true"/>
  <originating-identity-presentation-restriction active="true">
    <default-behaviour>presentation-restricted</default-behaviour>
  </originating-identity-presentation-restriction>
</simservs>"""
SIMSERVS_URL = "http://xdm/org.etsi.ngn.simservs/users/sip%3A1234%40foo.com/simservs.xml"

class TestXDM(unittest.TestCase):
    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.xdm.settings")
    def test_get_simservs(self, settings, AsyncHTTPClient):
        settings.XDM_URL = "xdm"
        client = Mock()
        AsyncHTTPClient.return_value = client

        callback = Mock()
        xdm.get_simservs(SIP_URI, callback)

        client.fetch.assert_called_once_with(SIMSERVS_URL,
                                             callback,
                                             method="GET",
                                             headers={"X-XCAP-Asserted-Identity": SIP_URI},
                                             allow_ipv6=True)

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.xdm.settings")
    def test_put_simservs(self, settings, AsyncHTTPClient):
        settings.XDM_URL = "xdm"
        client = Mock()
        AsyncHTTPClient.return_value = client

        callback = Mock()
        xdm.put_simservs(SIP_URI, XML, callback)

        client.fetch.assert_called_once_with(SIMSERVS_URL,
                                             callback,
                                             method="PUT",
                                             body=XML,
                                             headers={"X-XCAP-Asserted-Identity": SIP_URI},
                                             allow_ipv6=True)

    @patch("tornado.httpclient.AsyncHTTPClient")
    @patch("metaswitch.ellis.remote.xdm.settings")
    def test_delete_simservs(self, settings, AsyncHTTPClient):
        settings.XDM_URL = "xdm"
        client = Mock()
        AsyncHTTPClient.return_value = client

        callback = Mock()
        xdm.delete_simservs(SIP_URI, callback)

        client.fetch.assert_called_once_with(SIMSERVS_URL,
                                             callback,
                                             method="DELETE",
                                             headers={"X-XCAP-Asserted-Identity": SIP_URI},
                                             allow_ipv6=True)
