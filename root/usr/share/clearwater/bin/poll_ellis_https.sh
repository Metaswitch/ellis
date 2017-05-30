#!/bin/bash

# @file poll_ellis_https.sh
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

. /etc/clearwater/config
https_ip=$(/usr/share/clearwater/bin/bracket-ipv6-address $local_ip)

https_domain=${ellis_hostname:-ellis.$home_domain}
https_url=https://$https_domain/ping
ssl_cert_file=/etc/nginx/ssl/ellis.crt
ssl_key_file=/etc/nginx/ssl/ellis.key

if [ -e "$ssl_cert_file" ] && [ -e "$ssl_key_file" ]
then
  # Send HTTPS request and check that the response is "OK".
  curl -f -g -m 2 -s --resolve $https_domain:443:$https_ip --cacert $ssl_cert_file $https_url 2> /tmp/poll-ellis-https.sh.stderr.$$ | tee /tmp/poll-ellis-https.sh.stdout.$$ | head -1 | egrep -q "^OK$"
  rc=$?

else
  # SSL is not enabled, ignore.
  rc=0

fi

# Check the return code and log if appropriate.
if [ $rc != 0 ] ; then
  echo HTTP failed to $http_url    >&2
  cat /tmp/poll-ellis-https.sh.stderr.$$ >&2
  cat /tmp/poll-ellis-https.sh.stdout.$$ >&2
fi
rm -f /tmp/poll-ellis-https.sh.stderr.$$ /tmp/poll-ellis-https.sh.stdout.$$

exit $rc
