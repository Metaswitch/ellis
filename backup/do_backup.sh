#!/bin/bash

# @file do_backup.sh
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

BACKUP_DIR=/usr/share/clearwater/ellis/backup/backups
BACKUP_NAME=$(date +"%s")
BACKUP_FILE=db_backup.sql

mkdir -p $BACKUP_DIR

# Remove old backups (keeping last 3)
for f in $(ls -t $BACKUP_DIR | tail -n +4)
do
  echo "Deleting old backup: $BACKUP_DIR/$f"
  rm -r $BACKUP_DIR/$f
done

mkdir -p $BACKUP_DIR/$BACKUP_NAME
echo "Creating backup in $BACKUP_DIR/$BACKUP_NAME/$BACKUP_FILE"
mysqldump -u root ellis > $BACKUP_DIR/$BACKUP_NAME/$BACKUP_FILE
