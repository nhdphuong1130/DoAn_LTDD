#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -eu

if [ ! -f .env.example ]; then
  echo "Missing .env.example template!" >&2
  exit 1
fi

echo "Verifying .env.example syntax..."
grep -E '^[A-Z0-9_]+=' .env.example >/dev/null

echo ".env.example verified cleanly."
