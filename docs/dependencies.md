<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Dependencies Inventory

This document inventories all external upstream open-source dependencies across the backend, mobile, and infrastructure layers.

## Backend (Python 3.12)

Managed via `uv` in `backend/pyproject.toml` and locked in `backend/uv.lock`.

| Dependency | Version Floor | License | Rationale / Purpose |
|---|---|---|---|
| `fastapi` | `>=0.116,<1` | MIT | Asynchronous REST API framework |
| `uvicorn[standard]` | `>=0.35,<1` | BSD-3-Clause | ASGI web server runtime |
| `sqlalchemy` | `>=2.0.41,<3` | MIT | ORM and SQL abstraction |
| `pyodbc` | `>=5.2,<6` | MIT | High-performance ODBC driver for Microsoft SQL Server |
| `alembic` | `>=1.16,<2` | MIT | Database schema migration manager |
| `neo4j` | `>=5.28,<6` | Apache-2.0 | Official Bolt driver for Neo4j Knowledge Graph |
| `fastembed` | `>=0.8,<0.9` | Apache-2.0 | Fast, local CPU embedding inference (`BAAI/bge-small-en-v1.5`, 384d) |
| `minio` | `>=7.2,<8` | Apache-2.0 | S3-compatible client for lesson audio and image assets |
| `argon2-cffi` | `>=25.1,<26` | MIT | Secure password hashing using Argon2id |
| `PyJWT` | `>=2.10,<3` | MIT | JSON Web Token encoding and decoding |
| `pydantic-settings` | `>=2.10,<3` | MIT | Type-safe environment configuration management |
| `email-validator` | `>=2.2,<3` | CC0-1.0 | Email validation for student account registration |
| `pytest` | `>=8.4,<9` | MIT | Test framework (dev/test extra) |
| `pytest-cov` | `>=6.2,<7` | MIT | Code coverage reporting (dev/test extra) |
| `httpx2` | `>=2.13,<3` | BSD-3-Clause | TestClient HTTP transport (dev/test extra) |

## Mobile (Flutter / Dart)

Managed via `pubspec.yaml` in `mobile/`.

| Dependency | Version Floor | License | Rationale / Purpose |
|---|---|---|---|
| `flutter` | `>=3.27.0` | BSD-3-Clause | Cross-platform mobile UI framework |
| `http` | `^1.2.2` | BSD-3-Clause | Composable HTTP client for student API communication |
| `flutter_secure_storage` | `^9.2.2` | BSD-3-Clause | Encrypted local storage for student JWT access tokens |
| `audioplayers` | `^6.1.0` | MIT | Low-latency audio playback for listening tracks |
| `flutter_test` | SDK | BSD-3-Clause | Unit and widget test framework |

## Infrastructure & Services

Managed via Docker Compose (`infra/docker/compose.yaml`).

| Container Image | Upstream Version | License | Role |
|---|---|---|---|
| `mcr.microsoft.com/mssql/server` | `2022-latest` | Microsoft EULA (Express) | Relational database for accounts, curriculum structure, quizzes |
| `neo4j` | `5.26-community` | GPL-3.0 with Classpath Exception | Knowledge graph and dual vector search |
| `minio/minio` | `RELEASE.2025-02-07` | AGPL-3.0 | S3-compatible asset store for audio and images |
