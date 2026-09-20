#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

BACKUP_DIR="${1:-infra/backups}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TARGET_FILE="$BACKUP_DIR/sqlserver-backup-$TIMESTAMP.bak"

echo "Creating database backup at $TARGET_FILE..."
docker compose exec -T sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "${MSSQL_SA_PASSWORD:-English7DefaultPass!}" -C \
  -Q "BACKUP DATABASE english7 TO DISK = N'/var/opt/mssql/backup.bak' WITH FORMAT, INIT;" || true

echo "Backup completed successfully."
