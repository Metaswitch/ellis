#!/bin/bash

# @file do_backup.sh
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
