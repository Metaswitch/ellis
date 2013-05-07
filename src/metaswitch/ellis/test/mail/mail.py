# @file mail.py
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


from mock import patch, MagicMock, ANY, call
import unittest

from metaswitch.ellis.mail import mail

class TestMail(unittest.TestCase):
    _message = None

    @patch("metaswitch.ellis.settings.SMTP_SMARTHOST",             new="smtp.example.com")
    @patch("metaswitch.ellis.settings.SMTP_PORT",                  new=25)
    @patch("metaswitch.ellis.settings.SMTP_TIMEOUT_SEC",           new=10)
    @patch("metaswitch.ellis.settings.SMTP_USERNAME",              new="anonymous")
    @patch("metaswitch.ellis.settings.SMTP_PASSWORD",              new="password")
    @patch("metaswitch.ellis.settings.SMTP_USE_TLS",               new=True)
    @patch("metaswitch.ellis.settings.EMAIL_RECOVERY_SENDER",      new="no-reply@example.com")
    @patch("metaswitch.ellis.settings.EMAIL_RECOVERY_SENDER_NAME", new="Clearwater Automated Password Recovery")
    @patch("metaswitch.ellis.settings.EMAIL_RECOVERY_SIGNOFF",     new="The Clearwater Team")
    @patch("smtplib.SMTP")
    def test_mainline(self, smtp):
        address = "bob@example.com"
        full_name = "Robert Your Uncle"
        token = "deadbeef01&2"
        server = MagicMock()
        smtp.return_value = server
        self._message = None
        def dosave(x, y, z):
            self._message = z
        server.sendmail.side_effect = dosave
        
        urlbase = "https://www.example.com/forgotpassword?"
        mail.send_recovery_message(urlbase, address, full_name, token)

        smtp.assert_called_once_with(host = "smtp.example.com",
                                     port = 25,
                                     timeout = 10)
        server.starttls.assert_called_once_with()
        server.login.assert_called_once_with("anonymous", "password")
        server.sendmail.assert_called_once_with("no-reply@example.com", "bob@example.com", ANY)
        server.quit.assert_called_once_with()
        self.assertIn("please click on the link", self._message)
        self.assertIn("https://www.example.com/forgotpassword?email=bob%40example.com&token=deadbeef01%262", self._message)
        self.assertIn("https://www.example.com/forgotpassword?email=bob%40example.com&amp;token=deadbeef01%262", self._message)
        self.assertTrue(self._message.startswith("From: "), msg=">>" + self._message + "<<")
