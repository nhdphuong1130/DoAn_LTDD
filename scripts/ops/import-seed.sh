#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0
set -eu

env_file=${ENGLISH7_ENV_FILE:-.env}
docker compose --env-file "$env_file" run --rm api python -m english7.cli import-seed "$@"
