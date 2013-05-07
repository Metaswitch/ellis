use ellis;

-- ----------------------------------------------------------------------------
-- We'll need to use IF to determine whether the database is already upgraded.
-- MySQL only allows us to use IF from within stored procedures, so we'll
-- create a very short-lived stored procedure.  Before we do that, delete any
-- existing procedure.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS upgrade_ellis_database;

-- ----------------------------------------------------------------------------
-- Define the stored procedure.  Before doing this, we must redefine the
-- delimiter so that the end of statements within the body of the stored
-- procedure are not considered to be the end of the stored procedure as a
-- whole.
-- ----------------------------------------------------------------------------
DELIMITER $$
CREATE PROCEDURE upgrade_ellis_database()
BEGIN
  -- --------------------------------------------------------------------------
  -- Rename the global address book availability flag.
  -- --------------------------------------------------------------------------
  IF NOT EXISTS (SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='numbers' AND COLUMN_NAME='gab_listed') THEN
    ALTER TABLE numbers CHANGE COLUMN gab_availability gab_listed TINYINT NULL DEFAULT 0;
  END IF;

  -- --------------------------------------------------------------------------
  -- Add the expires field to the users table.
  -- --------------------------------------------------------------------------
  IF NOT EXISTS (SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='expires') THEN
    ALTER TABLE users ADD COLUMN expires datetime;
  END IF;

  -- --------------------------------------------------------------------------
  -- Add the PSTN flag to the numbers table.
  -- --------------------------------------------------------------------------
  IF NOT EXISTS (SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='numbers' AND COLUMN_NAME='pstn') THEN
    ALTER TABLE numbers ADD COLUMN pstn boolean NOT NULL DEFAULT False;
  END IF;

  -- --------------------------------------------------------------------------
  -- Add the password-recovery fields to the users table, and remove the 
  -- username field.
  -- --------------------------------------------------------------------------
  IF NOT EXISTS (SELECT *
                 FROM information_schema.COLUMNS
                 WHERE TABLE_SCHEMA=DATABASE() AND
                       TABLE_NAME='users' AND
                       COLUMN_NAME='recovery_token') THEN
     ALTER TABLE users
           DROP COLUMN username,
           ADD UNIQUE (email),
           ADD COLUMN recovery_token varchar(36),
           ADD COLUMN recovery_token_created datetime;
  END IF;

END $$
DELIMITER ;

  -- --------------------------------------------------------------------------
  -- Enlarge the maximum SIP URI value.
  -- --------------------------------------------------------------------------
  IF NOT EXISTS (SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='numbers' AND COLUMN_NAME='number' AND CHARACTER_OCTET_LENGTH=128) THEN
    ALTER TABLE numbers MODIFY number varchar(128);;
  END IF;

-- ----------------------------------------------------------------------------
-- Call the upgrade procedure and then drop it from the database.
-- ----------------------------------------------------------------------------
CALL upgrade_ellis_database();
DROP PROCEDURE upgrade_ellis_database;
