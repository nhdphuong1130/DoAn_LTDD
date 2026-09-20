<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Production Deployment Guide

This directory contains candidates and configurations for deploying the English 7 Grounded Learning Platform to cloud or on-premise single-node Linux servers (VPS).

## Architecture for Deployment

In production:
- External HTTPS traffic is terminated at a reverse proxy (e.g. Caddy or NGINX).
- The FastAPI application runs with multiple Uvicorn workers behind Gunicorn.
- SQL Server, Neo4j, and MinIO use persistent Docker volumes bound to high-speed storage.
- All secrets (JWT, database passwords, OpenRouter API keys) are supplied via environment variables or secret managers, never committed to git.

## Deployment Checklist

1. Clone repository to server.
2. Copy `.env.example` to `.env` and set secure, unique secrets.
3. Launch services: `docker compose -f infra/deploy/compose.production.yml up -d`.
4. Run database migrations: `docker compose -f infra/deploy/compose.production.yml exec api alembic upgrade head`.
5. Seed curriculum content: `docker compose -f infra/deploy/compose.production.yml exec api python -m english7.cli seed`.
