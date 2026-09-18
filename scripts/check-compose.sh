#!/usr/bin/env sh
set -eu

compose_file="${COMPOSE_FILE:-compose.yaml}"
env_file="${COMPOSE_ENV_FILE:-.env.example}"
required_services="api worker sqlserver neo4j minio minio-init"

docker compose --env-file "$env_file" -f "$compose_file" config --quiet
services="$(docker compose --env-file "$env_file" -f "$compose_file" config --services)"

for service in $required_services; do
  if ! printf '%s\n' "$services" | grep -Fxq "$service"; then
    printf 'Missing required service: %s\n' "$service" >&2
    exit 1
  fi
done

printf 'Compose services verified:\n%s\n' "$services"

