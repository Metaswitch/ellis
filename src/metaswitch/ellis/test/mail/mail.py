# @file mail.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


from mock import patch, MagicMock, ANY
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
