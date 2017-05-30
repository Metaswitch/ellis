# @file settings.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import os

"""
This file contains default settings for Homestead.  To override a setting
locally, create a file local_settings.py in this directory and add the override
setting to that.
"""

def ensure_dir_exists(d):
    """
    Creates the directory d if it doesn't exist.  Raises an exception iff the
    directory can't be created and didn't already exist.
    """
    try:
        os.makedirs(d)
    except Exception:
        pass
    if not os.path.isdir(d):
        raise RuntimeError("Failed to create dir %s" % d)

# Tornado configuration
TORNADO_PROCESSES_PER_CORE = 2

# Calculate useful directories relative to the project.
_MY_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(_MY_DIR, "..", "..", ".."))
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")
CERTS_DIR = os.path.join(PROJECT_DIR, "certificates")
STATIC_DIR = os.path.join(PROJECT_DIR, "web-content")

# Logging - log files will have names ellis-XXX.log, where XXX is the task id
LOG_FILE_PREFIX = "ellis"
LOG_FILE_MAX_BYTES = 10000000
LOG_BACKUP_COUNT = 10
PID_FILE = "/var/run/ellis/ellis.pid"

# Tornado cookie encryption key.  Tornado instances that share this key will
# all trust each other's cookies.
COOKIE_SECRET = 'secret'

# API key required for access to the web UI.
API_KEY = 'secret'

# Code that users who want to sign up must present.
SIGNUP_CODE = 'secret'

# SIP parameters
SIP_DIGEST_REALM = 'cw-ngv.com'

# MySQL Cluster configuration
SQL_HOST = "localhost"
SQL_USER = "root"
SQL_PORT = 5000
SQL_DB = "ellis"
SQL_PW = ""

# Homestead setup
HOMESTEAD_URL = "hs.cw-ngv.com:8889"

# XDM Server.
XDM_URL = "homer.cw-ngv.com:7888"

# UNIX domain socket prefix
HTTP_UNIX="/tmp/.ellis-sock"

# To avoid deploying with debug turned on, this settings should only ever be
# changed by creating a local_settings.py file in this directory.
TORNADO_DEBUG = False  # Make tornado emit debug messages to the browser etc.

# Throttling for password reset emails:
THROTTLER_EMAIL_RATE_PER_SECOND = 100.0 / (24 * 60 * 60)
THROTTLER_EMAIL_BURST = 5

# Throttling for password recovery attempts:
THROTTLER_RECOVER_RATE_PER_SECOND = 1
THROTTLER_RECOVER_BURST = 20

# Expiry token expires after this time.
RECOVERY_TOKEN_LIFETIME_SECS = 24 * 60 * 60

# General email settings:
SMTP_SMARTHOST="smtp.example.com"
SMTP_PORT=25
SMTP_TIMEOUT_SEC=10
SMTP_USERNAME="user"
SMTP_PASSWORD="password"
SMTP_USE_TLS=True

# Password recovery email settings:
EMAIL_RECOVERY_SENDER = "cw-admin@example.com"
EMAIL_RECOVERY_SENDER_NAME = "Clearwater Automated Password Recovery"
EMAIL_RECOVERY_SIGNOFF = "The Clearwater Team"
EMAIL_RECOVERY_PATH = "/resetpassword.html?"

# Include any locally-defined settings.
_local_settings_file = os.path.join(_MY_DIR, "local_settings.py")
if os.path.exists(_local_settings_file):
    execfile(_local_settings_file)

# Must do this after we've loaded the local settings, in case the paths change
ensure_dir_exists(LOGS_DIR)
