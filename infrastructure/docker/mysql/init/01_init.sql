-- docker/mysql/init/01_init.sql
-- Runs once on first container startup (docker-entrypoint-initdb.d)

SET NAMES utf8mb4;
SET character_set_client = utf8mb4;

-- Ensure the application database exists with correct charset
CREATE DATABASE IF NOT EXISTS `nexoradb`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `nexoradb`;

-- Example: create a migrations tracking table
CREATE TABLE IF NOT EXISTS `schema_migrations` (
  `version`    VARCHAR(255) NOT NULL,
  `applied_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Grant explicit privileges (user already created by MYSQL_USER env var)
GRANT ALL PRIVILEGES ON `nexoradb`.* TO 'appuser'@'%';
FLUSH PRIVILEGES;
