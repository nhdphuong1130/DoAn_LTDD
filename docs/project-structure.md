<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Project Structure

The English 7 Grounded Learning Platform is an open-source educational platform adhering to OLP 2026 monorepo architecture and Clean Architecture principles.

## Top-Level Layout

```text
.
├── .agents/             # AI coding agent guidelines and quality checklists
├── .github/             # GitHub actions workflows, issue and PR templates
├── backend/             # Python FastAPI backend service, GraphRAG engine, and tests
├── mobile/              # Flutter mobile student client application and tests
├── data/                # Curriculum datasets, textbook pages, and media metadata
├── evaluation/          # Retrieval-augmented generation evaluation ground truth
├── infra/               # Local Docker topologies, deployment manifests, and backup scripts
│   ├── docker/          # Local container compose definitions and service documentation
│   ├── deploy/          # Production deployment candidates and guides
│   └── backups/         # Destination for database recovery dumps (git-ignored)
├── scripts/             # Categorized repository automation scripts
│   ├── audit/           # Secret scans, config checks, and compose validation
│   ├── dev/             # Knowledge graph indexing and interactive query tests
│   └── ops/             # Database export, import, backup, and restore routines
├── docs/                # Architecture, API specifications, and operational guides
│   ├── architecture/    # Clean architecture baseline, GraphRAG pipeline, data models
│   ├── superpowers/     # Feature plans, specs, and verification records
│   ├── project-structure.md
│   └── dependencies.md
├── Makefile             # Canonical developer commands and build automation
├── AGENTS.md            # Agent instructions and pedagogical guardrails
├── CHANGELOG.md         # Version history following Keep a Changelog
├── CONTRIBUTING.md      # Contribution workflow and commit conventions
├── CODE_OF_CONDUCT.md   # Contributor Covenant v2.1
├── LICENSE              # Apache-2.0 License
├── SECURITY.md          # Vulnerability disclosure policy
├── .dockerignore        # Container build ignore rules
├── .env.example         # Environment template with dummy placeholders
└── README.md            # Project overview, badges, architecture, and quickstart
```

## Core Subsystems

### 1. Backend (`backend/`)
Built with Python 3.12, FastAPI, and uv:
- `src/english7/core/`: Application settings, security utilities (Argon2, JWT).
- `src/english7/db/`: SQLAlchemy ORM models, migrations, and session management.
- `src/english7/modules/`: Domain-driven feature modules:
  - `auth/`: Student authentication, registration, session management, and personal profile.
  - `knowledge/`: Knowledge Graph builder, curriculum ontology, and FastEmbed vector embeddings.
  - `retrieval/`: Multi-hop GraphRAG service, dual vector querying, and Reciprocal Rank Fusion (RRF).
  - `tutor/`: Grounded educational AI tutor with textbook citation enforcement.
  - `textbooks/`: Textbook structural hierarchy (Units, Sections, Activities, SourceFragments).
  - `quizzes/`: Quiz generation, question bank queries, and submission scoring.
  - `media/`: Audio streaming and textbook illustration asset serving.
- `tests/`: 160+ unit and integration tests verifying all modules.

### 2. Mobile (`mobile/`)
Built with Flutter (Dart 3.x):
- `lib/app/`: Application state management, navigation shell, and `StudentApi` contract.
- `lib/features/`:
  - `auth/`: Login and registration screens.
  - `lessons/`: Grade 7 curriculum lesson explorer, audio player, interactive exercise activities.
  - `quizzes/`: Timed quiz setup, limited audio playback, and score submission.
  - `tutor/`: Multi-turn conversational tutor with image selection and page citations.
  - `profile/`: Student profile dashboard (avatar, school, grade, bio, password update).
- `test/`: 33 unit, contract, and widget tests ensuring offline reliability.

### 3. Infrastructure (`infra/`)
- `infra/docker/`: Local development topology with Microsoft SQL Server 2022, Neo4j Community 5.26, MinIO, FastAPI API, and worker.
- `infra/deploy/`: Production deployment compose candidate with automated healthchecks and restarts.
- `infra/backups/`: Local directory for backup dumps.

### 4. Scripts (`scripts/`)
- `scripts/audit/`: Pre-commit scans for uncommitted secrets, developer-specific paths, and invalid configs.
- `scripts/dev/`: Scripts for building the full knowledge graph and running tutor benchmark queries.
- `scripts/ops/`: Operations scripts for exporting, importing, backing up, and restoring databases.
