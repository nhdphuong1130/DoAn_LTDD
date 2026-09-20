#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -eu

echo "Auditing compose configurations..."

if [ -f compose.yaml ]; then
  docker compose -f compose.yaml config --quiet
fi

if [ -f compose.integration.yaml ]; then
  docker compose -f compose.integration.yaml config --quiet
fi

if [ -f infra/docker/compose.yaml ]; then
  docker compose -f infra/docker/compose.yaml config --quiet
fi

echo "Docker compose configurations validated cleanly."
