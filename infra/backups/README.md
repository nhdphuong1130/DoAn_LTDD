<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Database Backups

This directory is the local destination for database recovery dumps and backup sets for SQL Server, Neo4j, and MinIO storage.

Backup files (`*.bak`, `*.dump`, `*.tar.gz`) are ignored by git to protect data privacy and keep repository size minimal.

## Backup Commands

```bash
# Export relational seed dataset
make db-export-seed

# Import relational seed dataset
make db-import-seed
```
