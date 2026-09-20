<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Clean Architecture Review

Use this checklist before committing or reviewing backend or mobile architecture changes.

## Layer Boundaries

- [ ] **Domain Isolation**: Domain entities, ontology models, and data types do not import FastAPI, SQLAlchemy, Flutter widgets, or database drivers.
- [ ] **Inward Dependency Rule**: Outer layers (routers, CLI, UI screens) depend on inner layer interfaces and services, never the reverse.
- [ ] **No Business Logic in Routes**: FastAPI router functions only validate input envelopes, invoke services, and return DTO response schemas.
- [ ] **No Direct Queries in Services**: Database querying is abstracted behind repository classes.
- [ ] **Repository Purity**: Repository classes perform persistence and queries without enforcing high-level business workflow policies.

## Mobile Architecture (Flutter)

- [ ] **Feature-First Structure**: New UI components reside in their owning `features/<name>/` directory.
- [ ] **Contract Driven**: Client communicates with backend strictly via `StudentApi` contract interfaces.
- [ ] **Lifecycle Safety**: Asynchronous calls check `if (!mounted) return;` before calling `setState`.
- [ ] **State Representation**: Screens cleanly handle `loading`, `error`, `empty`, and `success` states.

## Testing & Quality

- [ ] Unit tests cover service and domain logic without requiring live network or external databases.
- [ ] Integration tests are isolated and annotated with `@pytest.mark.integration`.
- [ ] Flutter widget tests verify interactive behavior and pump cycles (`pumpAndSettle`).
