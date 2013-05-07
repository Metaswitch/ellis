#!/usr/bin/python

# @file utils.py
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


from mock import Mock
import unittest

from metaswitch.ellis.api.utils import HTTPCallbackGroup

def mock_resp(code=200, method="GET"):
    resp = Mock()
    resp.code = code
    resp.request.method = method
    return resp

class TestHTTPCallbackGroup(unittest.TestCase):
    def setUp(self):
        super(TestHTTPCallbackGroup, self).setUp()
        self.on_success = Mock()
        self.on_failure = Mock()
        self.group = HTTPCallbackGroup(self.on_success, self.on_failure)

    def test_get_callback(self):
        cb = self.group.callback()
        cb2 = self.group.callback()
        self.assertTrue(cb in self.group._live_callbacks)
        resp = mock_resp()
        cb(resp)
        self.assertFalse(cb in self.group._live_callbacks)
        self.assertTrue(cb2 in self.group._live_callbacks)
        self.assertTrue(resp in self.group.responses)

    def test_finish_success(self):
        cb = self.group.callback()
        cb2 = self.group.callback()
        self.assertFalse(self.on_failure.called)
        self.assertFalse(self.on_success.called)
        resp = mock_resp()
        cb(resp)
        self.assertFalse(self.on_failure.called)
        self.assertFalse(self.on_success.called)
        resp2 = mock_resp()
        cb2(resp2)
        self.assertFalse(self.on_failure.called)
        self.on_success.assert_called_once_with([resp, resp2])

    def test_finish_success_delete_404(self):
        cb = self.group.callback()
        cb2 = self.group.callback()
        self.assertFalse(self.on_failure.called)
        self.assertFalse(self.on_success.called)
        resp = mock_resp(code=404, method="DELETE")
        cb(resp)
        self.assertFalse(self.on_failure.called)
        self.assertFalse(self.on_success.called)
        resp2 = mock_resp()
        cb2(resp2)
        self.assertFalse(self.on_failure.called)
        self.on_success.assert_called_once_with([resp, resp2])

    def test_finish_failure(self):
        cb = self.group.callback()
        cb2 = self.group.callback()
        resp = mock_resp(404)
        cb(resp)
        self.on_failure.assert_called_once_with(resp)
        self.assertFalse(self.on_success.called)
        self.on_failure.reset_mock()
        resp2 = mock_resp()
        cb2(resp2)
        self.assertFalse(self.on_failure.called)
        self.assertFalse(self.on_success.called)



if __name__ == "__main__":
    unittest.main()
