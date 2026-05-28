CREATE DATABASE IF NOT EXISTS todo_log
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE todo_log;

CREATE TABLE IF NOT EXISTS query_log (
    `type` VARCHAR(20) NOT NULL,
    `sql` TEXT NOT NULL,
    `dateime` DATETIME NOT NULL
);

CREATE USER IF NOT EXISTS 'todo_logger'@'%' IDENTIFIED BY 'todo_logger_pw';
GRANT INSERT, SELECT, CREATE ON todo_log.* TO 'todo_logger'@'%';
FLUSH PRIVILEGES;
