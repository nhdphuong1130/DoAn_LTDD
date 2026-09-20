#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT/backend"

if [ -f "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
else
  UV="uv"
fi

echo "Testing grounded tutor queries..."
$UV run python scripts/test_tutor_queries.py
