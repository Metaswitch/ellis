#!/bin/bash

# @file restore_backup.sh
#
# Copyright (C) Metaswitch Networks 2015
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

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
