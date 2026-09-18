#!/usr/bin/env sh
set -eu

failed=0

check() {
  description=$1
  pattern=$2
  shift 2
  if rg -n "$pattern" "$@"; then
    echo "$description" >&2
    failed=1
  fi
}

check "Developer-specific absolute path detected." '/home/[^/]+/' backend/src mobile/lib
check "Mobile source contains a hardcoded network host." '(https?://|10\.0\.2\.2|127\.0\.0\.1|localhost)' mobile/lib
check "Mobile source accesses infrastructure directly." '(pyodbc|neo4j|mssql|sqlserver|minio|openrouter)' mobile/lib
check "OpenRouter calls must remain in the provider adapter." 'openrouter\.ai' backend/src
check "Mobile quiz policy must come from the API." '(\[15, *45, *60\]|remainingPlays *= *2|maxAudioPlays *= *2)' mobile/lib

if [ "$failed" -ne 0 ]; then
  exit 1
fi

echo "Hardcoded configuration scan passed."
