-- SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
-- SPDX-License-Identifier: Apache-2.0

IF DB_ID(N'english7') IS NULL
BEGIN
    CREATE DATABASE english7 COLLATE Latin1_General_100_BIN2_UTF8;
END;
GO
