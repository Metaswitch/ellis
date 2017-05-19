# @file mail.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import smtplib
import logging
import random
import urllib
import string
from tornado.template import Template
from pkg_resources import resource_string

from metaswitch.ellis import settings

_log = logging.getLogger("ellis.mail")

_template = Template(resource_string(__name__, "forgotpassword.eml"))

def send_recovery_message(urlbase, address, full_name, token):
    """Send a recovery message to the user.

    urlbase - Prefix of URL to insert into email.  Will have
    email=blah&token=blah appended to it.

    address - email address to send message to.

    full_name - full name to address email to.

    token - token to include in email.
    """
    _log.info("Sending recovery message to %s: token is '%s'", address, token)
    
    link = "%semail=%s&token=%s" % (urlbase,
                                    urllib.quote_plus(address),
                                    urllib.quote_plus(token))
    boundary = string.join((random.choice(string.letters) for i in xrange(16)), '')

    message = _template.generate(from_    = settings.EMAIL_RECOVERY_SENDER,
                                 fromname = settings.EMAIL_RECOVERY_SENDER_NAME,
                                 to       = address,
                                 name     = full_name,
                                 link     = link,
                                 signoff  = settings.EMAIL_RECOVERY_SIGNOFF,
                                 boundary = boundary)
    message_bytes = message.encode("utf-8")

    try:
        server = smtplib.SMTP(
            host = settings.SMTP_SMARTHOST,
            port = settings.SMTP_PORT,
            timeout = settings.SMTP_TIMEOUT_SEC)
        server.set_debuglevel(_log.isEnabledFor(logging.DEBUG))
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.ehlo()  # @@@KSW apparently - seems silly to me
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_RECOVERY_SENDER, address, message_bytes)
        server.quit()
    except smtplib.SMTPException as e: # pragma: no cover
        _log.error("Unable to send email to %s via %s/%s/%s: %s", address, 
                   settings.SMTP_SMARTHOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, e)
        raise e
    else:
        _log.info("Sent email to %s", address)
