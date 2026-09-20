# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0

COMPOSE_ENV := $(if $(wildcard .env),--env-file .env,)
COMPOSE := docker compose $(COMPOSE_ENV) -f compose.yaml
UV := $(shell which uv 2>/dev/null || echo $(HOME)/.local/bin/uv)
FLUTTER := $(shell which flutter 2>/dev/null || echo $(HOME)/.local/opt/flutter/bin/flutter)

.PHONY: help up down logs restart test test-backend test-mobile analyze audit seed db-backup db-restore clean

help:
	@echo "English 7 Grounded Learning Platform - Developer Commands"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up            Start local Docker services (SQL Server, Neo4j, MinIO, API, Worker)"
	@echo "  make down          Stop Docker services cleanly"
	@echo "  make logs          Follow container logs"
	@echo "  make restart       Restart Docker services"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          Run both backend and mobile test suites"
	@echo "  make test-backend  Run backend unit and modular pytest suite"
	@echo "  make test-mobile   Run Flutter widget and unit tests"
	@echo "  make analyze       Run Flutter static code analysis"
	@echo "  make audit         Run repository security, secret, and config audits"
	@echo ""
	@echo "Data & Operations:"
	@echo "  make seed          Seed curriculum data and knowledge graph"
	@echo "  make db-backup     Create database backup dump"
	@echo "  make db-restore    Restore database from latest backup"
	@echo "  make clean         Remove build and cache artifacts"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs -f

restart: down up

test: test-backend test-mobile

test-backend:
	cd backend && $(UV) run pytest tests --ignore=tests/integration -q

test-mobile:
	cd mobile && $(FLUTTER) test

analyze:
	cd mobile && $(FLUTTER) analyze

audit:
	./scripts/audit/check-no-secrets.sh
	./scripts/audit/check-no-hardcoded-config.sh
	./scripts/audit/env-example-check.sh
	./scripts/audit/check-compose.sh

seed:
	cd backend && $(UV) run python -m english7.cli seed
	./scripts/dev/build-full-knowledge-graph.sh

db-backup:
	./scripts/ops/backup-db.sh

db-restore:
	./scripts/ops/restore-db.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf mobile/build mobile/.dart_tool 2>/dev/null || true
