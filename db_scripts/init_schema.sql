-- SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
-- SPDX-License-Identifier: Apache-2.0

IF DB_ID(N'english7') IS NULL
BEGIN
    CREATE DATABASE english7 COLLATE Latin1_General_100_BIN2_UTF8;
END;
GO

USE english7;
GO

IF OBJECT_ID('users', 'U') IS NOT NULL
BEGIN
    IF COL_LENGTH('users', 'full_name') IS NULL ALTER TABLE users ADD full_name NVARCHAR(255) NULL;
    IF COL_LENGTH('users', 'date_of_birth') IS NULL ALTER TABLE users ADD date_of_birth DATE NULL;
    IF COL_LENGTH('users', 'gender') IS NULL ALTER TABLE users ADD gender VARCHAR(30) NULL;
    IF COL_LENGTH('users', 'school_name') IS NULL ALTER TABLE users ADD school_name NVARCHAR(255) NULL;
    IF COL_LENGTH('users', 'class_name') IS NULL ALTER TABLE users ADD class_name NVARCHAR(100) NULL;
END;
GO
