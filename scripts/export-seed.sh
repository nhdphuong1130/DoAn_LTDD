#!/usr/bin/env sh
set -eu

env_file=${ENGLISH7_ENV_FILE:-.env}
docker compose --env-file "$env_file" run --rm api python -m english7.cli export-seed "$@"
