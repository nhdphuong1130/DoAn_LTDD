#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -eu

scan_paths="backend/src mobile/lib scripts infra docs compose.yaml .env.example"
pattern='(sk-or-v1-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer [A-Za-z0-9_-]{24,})'

if command -v rg >/dev/null 2>&1; then
  if rg -n --hidden --glob '!*check-no-secrets.sh' "$pattern" $scan_paths; then
    echo "Potential committed secret detected." >&2
    exit 1
  fi
else
  if grep -EnR --exclude="*check-no-secrets.sh" "$pattern" $scan_paths; then
    echo "Potential committed secret detected." >&2
    exit 1
  fi
fi

echo "Secret audit passed cleanly."
