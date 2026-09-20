<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Agent Instructions

These instructions apply to AI coding assistants and autonomous agents working in this repository.

## Project Mission & Core Principles

The **English 7 Grounded Learning Platform** is an educational AI system grounded directly in the Vietnamese Grade 7 English curriculum (*Tiếng Anh 7 Global Success*). Every explanation, quiz, or tutor answer must be rigorously grounded with page numbers and textbook citations.

## Clean Architecture & Code Organization

- **Backend (`backend/src/english7/`)**:
  - `core/`: Settings, configuration, security tokens, and hashing.
  - `db/`: SQLAlchemy declarative models and session lifecycle.
  - `modules/`: Modular features organized by domain (`auth`, `knowledge`, `retrieval`, `tutor`, `textbooks`, `quizzes`, `media`, `attempts`, `seeding`, `jobs`, `admin`, `ai`).
  - Presentation (FastAPI routers) and infrastructure (Neo4j, MinIO, SQL Server) depend on domain models and service interfaces, never the reverse.
  - Business logic belongs in service classes, not route handlers.

- **Mobile (`mobile/lib/`)**:
  - `app/`: Application bootstrap, routing, and student API interface contracts (`StudentApi`).
  - `features/`: Feature-first modular Flutter code (`auth`, `lessons`, `quizzes`, `tutor`, `profile`, `progress`).
  - `shared/` & `widgets/`: Shared UI components, theme tokens, and audio players.

## Open-Source Readiness (OLP Standard)

- Maintain Apache-2.0 licensing and SPDX headers across all new code and documentation.
- Keep build, test, and check commands runnable completely from source via the root `Makefile`.
- Document all new dependencies in `docs/dependencies.md`.
- Never commit secrets, real API keys, credentials, or `.env` files.
- Always run `make test` and `make analyze` before finalizing work.

## Pedagogical Guardrails

- **Grounding Required**: AI tutor responses MUST cite textbook unit and page (`[Unit X, Page Y]`).
- **Pedagogical Ontology**: Use established curriculum ontology nodes (`Topic`, `GrammarRule`, `Vocabulary`, `PronunciationSound`).
- **Safe Authentication**: Enforce role-based access in backend router dependencies, not solely in client UI.
- **Atomic Commits**: Keep commits focused and accompanied by tests and changelog updates.
