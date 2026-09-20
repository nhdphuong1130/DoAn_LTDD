#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

project="english7-knowledge-integration"
compose_file="compose.integration.yaml"

cleanup() {
  docker compose -p "$project" -f "$compose_file" down -v --remove-orphans
}
trap cleanup EXIT

docker compose -p "$project" -f "$compose_file" up \
  --build --abort-on-container-exit --exit-code-from knowledge-tests
