CREATE DATABASE IF NOT EXISTS ellis;
USE ellis;

CREATE TABLE IF NOT EXISTS numbers (
    number_id varbinary(36) PRIMARY KEY,
    number varchar(36) NOT NULL UNIQUE,
    owner_id varbinary(36) NULL,
    gab_listed TinyInt NOT NULL DEFAULT 1,
    pstn boolean NOT NULL DEFAULT False,
    INDEX (owner_id)
);

CREATE TABLE IF NOT EXISTS users (
    user_id varbinary(36) PRIMARY KEY,
    password CHAR(64) BINARY NOT NULL,
    full_name varchar(36) NOT NULL,
    email varchar(36) NOT NULL UNIQUE,
    expires datetime,
    recovery_token varchar(36),
    recovery_token_created datetime
);

