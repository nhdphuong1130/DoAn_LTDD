#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -eu

failed=0

search() {
  pattern=$1
  shift
  if command -v rg >/dev/null 2>&1; then
    rg -n "$pattern" "$@"
  else
    grep -EnR --exclude-dir="__pycache__" --exclude-dir=".pytest_cache" --exclude-dir=".git" "$pattern" "$@"
  fi
}

check() {
  description=$1
  pattern=$2
  shift 2
  if search "$pattern" "$@"; then
    echo "$description" >&2
    failed=1
  fi
}

check "Developer-specific absolute path detected." '/home/[^/]+/' backend/src mobile/lib
check "Mobile source accesses infrastructure directly." '(pyodbc|neo4j|mssql|sqlserver|minio|openrouter)' mobile/lib
check "OpenRouter calls must remain in the provider adapter." 'openrouter\.ai' backend/src/english7/modules/ai

if [ "$failed" -ne 0 ]; then
  exit 1
fi

echo "Hardcoded configuration audit passed cleanly."
