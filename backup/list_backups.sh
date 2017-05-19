#!/bin/bash

# @file list_backups.sh
#
# Copyright (C) Metaswitch Networks
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

if [ ! -d $BACKUP_DIR ]
then
  die "Backup directory does not exist"
fi

echo "Backups for ellis:"
for f in $(ls -t $BACKUP_DIR)
do
  echo "$f $BACKUP_DIR/$f"
done | column -t
