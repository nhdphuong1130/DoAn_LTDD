# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0

-include .env
COMPOSE := docker compose -f docker-compose.yml
DB_NAME := english7
DB_USER := sa
DB_PASSWORD ?= $(if $(SQLSERVER_SA_PASSWORD),$(SQLSERVER_SA_PASSWORD),$(if $(MSSQL_SA_PASSWORD),$(MSSQL_SA_PASSWORD),English7DefaultPass!))
BACKUP_DIR := backups
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)
BACKUP_BAK := $(DB_NAME)_$(TIMESTAMP).bak
BACKUP_SQL := $(DB_NAME)_$(TIMESTAMP).sql
SQLCMD := /opt/mssql-tools18/bin/sqlcmd -S localhost -U $(DB_USER) -P "$(DB_PASSWORD)" -C

UV := $(shell which uv 2>/dev/null || echo $(HOME)/.local/bin/uv)
FLUTTER := $(shell which flutter 2>/dev/null || echo $(HOME)/.local/opt/flutter/bin/flutter)

.PHONY: help up down ps logs restart backup-db restore test test-backend test-mobile analyze seed clean

help:
	@echo "English 7 Grounded Learning Platform - Lệnh quản trị & phát triển"
	@echo ""
	@echo "Docker & Dịch vụ:"
	@echo "  make up            Khởi động toàn bộ container (SQL Server, Neo4j, MinIO, API, Worker)"
	@echo "  make down          Dừng cụm container"
	@echo "  make ps            Xem trạng thái các container"
	@echo "  make logs          Xem live logs của cụm container"
	@echo "  make restart       Khởi động lại toàn bộ dịch vụ"
	@echo ""
	@echo "Cơ sở dữ liệu (Backups & Restore):"
	@echo "  make backup-db     Sao lưu toàn bộ SQL Server thành file .bak và .sql trong backups/"
	@echo "  make restore FILE=backups/<file>  Khôi phục CSDL từ file .bak hoặc .sql"
	@echo ""
	@echo "Kiểm thử & Chất lượng mã nguồn:"
	@echo "  make test          Chạy toàn bộ kiểm thử backend và mobile"
	@echo "  make test-backend  Chạy bộ kiểm thử backend pytest"
	@echo "  make test-mobile   Chạy bộ kiểm thử mobile Flutter test"
	@echo "  make analyze       Chạy phân tích tĩnh Flutter analyze"
	@echo ""
	@echo "Dữ liệu tri thức:"
	@echo "  make seed          Nạp dữ liệu SGK và build Knowledge Graph trong Neo4j"
	@echo "  make clean         Xóa bỏ cache và file build tạm"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down --remove-orphans

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

restart: down up

backup-db:
	mkdir -p $(BACKUP_DIR)
	$(COMPOSE) exec -T sqlserver mkdir -p /var/opt/mssql/backup
	$(COMPOSE) exec -T sqlserver $(SQLCMD) -Q "BACKUP DATABASE [$(DB_NAME)] TO DISK = N'/var/opt/mssql/backup/$(BACKUP_BAK)' WITH INIT, COPY_ONLY"
	$(COMPOSE) cp sqlserver:/var/opt/mssql/backup/$(BACKUP_BAK) $(BACKUP_DIR)/$(BACKUP_BAK)
	printf '%s\n' \
		"-- Generated restore helper for $(DB_NAME)" \
		"-- Preferred full restore artifact: $(BACKUP_BAK)" \
		"-- Use: make restore FILE=$(BACKUP_DIR)/$(BACKUP_BAK)" \
		"SELECT '$(DB_NAME)' AS database_name, '$(BACKUP_BAK)' AS backup_file;" \
		> $(BACKUP_DIR)/$(BACKUP_SQL)
	@echo "Sao lưu thành công vào $(BACKUP_DIR)/$(BACKUP_BAK)"

restore:
	@test -n "$(FILE)" || (echo "Sử dụng: make restore FILE=$(BACKUP_DIR)/<file.sql|file.bak>"; exit 1)
	@case "$(FILE)" in \
	  *.bak) \
	    cp "$(FILE)" /tmp/restore.bak && \
	    $(COMPOSE) exec -T sqlserver mkdir -p /var/opt/mssql/backup && \
	    $(COMPOSE) cp /tmp/restore.bak sqlserver:/var/opt/mssql/backup/restore.bak && \
	    $(COMPOSE) exec -T sqlserver $(SQLCMD) -Q "USE master; IF DB_ID('$(DB_NAME)') IS NOT NULL BEGIN ALTER DATABASE [$(DB_NAME)] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [$(DB_NAME)]; END; RESTORE DATABASE [$(DB_NAME)] FROM DISK = N'/var/opt/mssql/backup/restore.bak' WITH MOVE '$(DB_NAME)' TO '/var/opt/mssql/data/$(DB_NAME).mdf', MOVE '$(DB_NAME)_log' TO '/var/opt/mssql/data/$(DB_NAME)_log.ldf', REPLACE";; \
	  *.sql) \
	    $(COMPOSE) exec -T sqlserver $(SQLCMD) -d $(DB_NAME) -i /dev/stdin < "$(FILE)";; \
	  *) \
	    echo "Không hỗ trợ định dạng file: $(FILE)"; exit 1;; \
	esac
	@echo "Khôi phục CSDL thành công từ $(FILE)"

test: test-backend test-mobile

test-backend:
	cd backend && $(UV) run pytest tests --ignore=tests/integration -q

test-mobile:
	cd mobile && $(FLUTTER) test

analyze:
	cd mobile && $(FLUTTER) analyze

seed:
	cd backend && $(UV) run python -m english7.cli seed
	./scripts/build_full_knowledge_graph.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf mobile/build mobile/.dart_tool 2>/dev/null || true
