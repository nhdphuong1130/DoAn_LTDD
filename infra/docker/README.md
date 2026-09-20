<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Local Docker Infrastructure

This directory documents and manages local infrastructure containers for the English 7 Grounded Learning Platform.

## Services & Ports

| Service | Technology | Port (Host:Container) | Description |
|---|---|---|---|
| `sqlserver` | Microsoft SQL Server 2022 | `1433:1433` | Primary relational database for user authentication, textbook metadata, student attempts, and quizzes |
| `neo4j` | Neo4j Community 5.26 | `7474:7474`, `7687:7687` | Pedagogical Knowledge Graph & dual vector search (HTTP & Bolt) |
| `minio` | MinIO Object Storage | `9000:9000`, `9001:9001` | S3-compatible media asset storage (lesson audio tracks & textbook illustrations) |
| `api` | FastAPI Python 3.12 | `8000:8000` | Core backend REST API & Retrieval Engine |
| `worker` | Python 3.12 background worker | N/A (Internal) | Asynchronous ingestion and knowledge graph build jobs |

## Environment

Local development configuration is driven by `.env` in the repository root (see `.env.example`).

## Developer Commands

```bash
# Start all services in background
make up

# Follow live container logs
make logs

# Shut down services cleanly
make down
```
