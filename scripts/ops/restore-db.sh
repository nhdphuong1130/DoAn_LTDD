#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

BACKUP_FILE="${1:-infra/backups/latest.bak}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file $BACKUP_FILE not found." >&2
  exit 1
fi

echo "Restoring database from $BACKUP_FILE..."
docker compose exec -T sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "${MSSQL_SA_PASSWORD:-English7DefaultPass!}" -C \
  -Q "RESTORE DATABASE english7 FROM DISK = N'/var/opt/mssql/backup.bak' WITH REPLACE;" || true

echo "Database restore completed."
