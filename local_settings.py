# @file local_settings.py
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

STATIC_DIR = "/usr/share/clearwater/ellis/web-content"
XDM_DEFAULT_SIMSERVS_FILE = "/usr/share/clearwater/ellis/common/metaswitch/common/default_simservs.xml"
LOGS_DIR = "/var/log/ellis"
PID_FILE = "/var/run/ellis/ellis.pid"
ALLOW_HTTP = True
SIP_DIGEST_REALM = ""
HOMESTEAD_URL = ""
XDM_URL = ""
SMTP_SMARTHOST = "smtp.example.com"
SMTP_PORT = 25
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
SMTP_USE_TLS = True
EMAIL_RECOVERY_SENDER = "cw-admin@example.com"
SIGNUP_CODE = ""
COOKIE_SECRET = ""
API_KEY = ""
