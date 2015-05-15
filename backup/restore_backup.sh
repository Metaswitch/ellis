#!/bin/bash

# @file restore_backup.sh
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

die () {
  echo >&2 "$@"
  exit 1
}

BACKUP_DIR=/usr/share/clearwater/ellis/backup/backups
BACKUP_NAME=$1
BACKUP_FILE=db_backup.sql

if [[ -z "$BACKUP_NAME" ]]
then
  echo "No backup specified, will attempt to backup from latest"
else
  echo "Will attempt to backup from backup $BACKUP_NAME"
fi

# First make sure we have a backup to backup from
if [ -d $BACKUP_DIR ]
then
  if [[ -z $BACKUP_NAME ]]
  then
    echo "Usage: restore_backup.sh <backup>"
    echo "No valid backup specified, will attempt to backup from latest. You can list available backups with list_backups.sh"
    BACKUP_NAME=$(ls -t $BACKUP_DIR | head -1)
  elif [ -d "$BACKUP_DIR/$BACKUP_NAME" ]
  then
    echo "Found backup directory $BACKUP_NAME"
  else
    die "Could not find specified backup directory, use list_backups to see available backups"
  fi 
else
  die "Backup directory does not exist"
fi

# We've made sure all the backup exists, proceed with backup
echo "Restoring backup for ellis..."

# Stop monit from restarting ellis while we restore
# It isn't strictly necessary to stop ellis, however leaving it running makes the backup a
# lot slower as ellis prevents tables being dropped immediately by being connected to mysql
monit stop -g ellis 
service ellis stop
mysql -v -u root ellis < $BACKUP_DIR/$BACKUP_NAME/$BACKUP_FILE
monit start -g ellis || service ellis start
