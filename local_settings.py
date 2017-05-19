# @file local_settings.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

LOCAL_IP = MUST_BE_CONFIGURED
STATIC_DIR = "/usr/share/clearwater/ellis/web-content"
LOGS_DIR = "/var/log/ellis"
PID_FILE = "/var/run/ellis/ellis.pid"
SIP_DIGEST_REALM = MUST_BE_CONFIGURED
HOMESTEAD_URL = MUST_BE_CONFIGURED
XDM_URL = MUST_BE_CONFIGURED
SMTP_SMARTHOST = "smtp.example.com"
SMTP_PORT = 25
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
SMTP_USE_TLS = True
EMAIL_RECOVERY_SENDER = "cw-admin@example.com"
SIGNUP_CODE = ""
COOKIE_SECRET = ""
API_KEY = ""
