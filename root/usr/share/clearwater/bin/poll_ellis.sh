#!/bin/bash

# @file poll_ellis.sh
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

. /etc/clearwater/config
http_ip=$(/usr/share/clearwater/bin/bracket-ipv6-address $local_ip)

http_url=http://$http_ip/ping
ssl_cert_file=/etc/nginx/ssl/ellis.crt
ssl_key_file=/etc/nginx/ssl/ellis.key

if [ -e "$ssl_cert_file" ] && [ -e "$ssl_key_file" ]
then
  # Send HTTP request and check that a 301 response is sent
  curl -f -g -m 2 -s $http_url -o /dev/null -w "%{http_code}" 2> /tmp/poll-ellis.sh.stderr.$$ | tee /tmp/poll-ellis.sh.stdout.$$ | egrep -q "^301$"
  rc=$?

else
  # Send HTTP request and check that the response is "OK".
  curl -f -g -m 2 -s $http_url 2> /tmp/poll-ellis.sh.stderr.$$ | tee /tmp/poll-ellis.sh.stdout.$$ | head -1 | egrep -q "^OK$"
  rc=$?

fi

# Check the return code and log if appropriate.
if [ $rc != 0 ] ; then
  echo HTTP failed to $http_url    >&2
  cat /tmp/poll-ellis.sh.stderr.$$ >&2
  cat /tmp/poll-ellis.sh.stdout.$$ >&2
fi
rm -f /tmp/poll-ellis.sh.stderr.$$ /tmp/poll-ellis.sh.stdout.$$

exit $rc
