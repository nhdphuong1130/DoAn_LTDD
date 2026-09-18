#!/usr/bin/env sh
set -eu

scan_paths="backend/src mobile/lib scripts compose.yaml"
pattern='(sk-or-v1-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer [A-Za-z0-9_-]{24,})'

if command -v rg >/dev/null 2>&1; then
  if rg -n --hidden --glob '!check-no-secrets.sh' "$pattern" $scan_paths; then
    echo "Potential committed secret detected." >&2
    exit 1
  fi
else
  if grep -EnR --exclude="check-no-secrets.sh" "$pattern" $scan_paths; then
    echo "Potential committed secret detected." >&2
    exit 1
  fi
fi

echo "Secret scan passed."
