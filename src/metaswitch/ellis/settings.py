# @file settings.py
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

import os
import logging

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
DATA_DIR = os.path.join(PROJECT_DIR, "data")
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")
CERTS_DIR = os.path.join(PROJECT_DIR, "certificates")
STATIC_DIR = os.path.join(PROJECT_DIR, "web-content")

# Logging - log files will have names ellis-XXX.log, where XXX is the task id
LOG_FILE_PREFIX = "ellis"
LOG_FILE_MAX_BYTES = 10000000
LOG_BACKUP_COUNT = 10
LOG_LEVEL = logging.INFO
PID_FILE = os.path.join(PROJECT_DIR, "server.pid")

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
XDM_DEFAULT_SIMSERVS_FILE = os.path.join(_MY_DIR, "../../../common/metaswitch/common/default_simservs.xml")

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
ensure_dir_exists(DATA_DIR)
ensure_dir_exists(LOGS_DIR)
