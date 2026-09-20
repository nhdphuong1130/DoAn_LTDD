# Standardize Project Structure to OLP_Demo Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize `DoAN_LTDD` repository structure to match the open-source engineering standards of `OLP_Demo` (Olympic Tin học / OLP 2026 standard), establishing professional governance, agent checklists, CI workflows, categorized scripts, infrastructure layout, Makefile, and architectural documentation while preserving `backend/` and `mobile/` at the root.

**Architecture:** Monorepo architecture following Clean Architecture principles. Root level maintains client app (`mobile/`) and backend services (`backend/`), supplemented with standardized top-level directories: `.agents/` for AI safety and quality checklists, `.github/` for CI/CD and templates, `infra/` for Docker and deployment topologies, `scripts/` segmented into `audit/`, `dev/`, and `ops/`, and `docs/` for project structure and architecture specs. Developer workflows are orchestrated via a root `Makefile`.

**Tech Stack:** Python 3.12 (FastAPI, SQLAlchemy, Neo4j, FastEmbed, Pytest), Flutter 3.x / Dart (Mobile), Docker Compose, GitHub Actions, Make, Markdown.

**Spec:** User selected option to preserve `backend/` and `mobile/` in place and standardize all governance, infrastructure, scripts, documentation, and agent workflows to match `/home/nguyenphuong/Documents/OLP_Demo`.

## Global Constraints

- Do NOT delete or break existing application functionality or tests in `backend/` or `mobile/`.
- All 163 backend tests and 33 mobile tests MUST continue to pass (100% green).
- Keep `compose.yaml` runnable from root as well as through `infra/docker/` and `Makefile`.
- Adhere strictly to OSI-approved Apache-2.0 license standards and SPDX headers.
- Provide clean, deterministic `make` targets.

---

### Task 1: Governance & Open-Source Community Files

**Files:**
- Create: `AGENTS.md`
- Create: `CHANGELOG.md`
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `LICENSE`
- Create: `SECURITY.md`
- Create: `.dockerignore`

- [ ] **Step 1: Create `LICENSE` with Apache-2.0**
- [ ] **Step 2: Create `CODE_OF_CONDUCT.md` with Contributor Covenant v2.1**
- [ ] **Step 3: Create `CONTRIBUTING.md` with conventional commits, code style, and test guidelines**
- [ ] **Step 4: Create `SECURITY.md` with vulnerability reporting policy**
- [ ] **Step 5: Create `CHANGELOG.md` following Keep a Changelog standard**
- [ ] **Step 6: Create `AGENTS.md` with AI coding agent guidelines, clean architecture, and product guardrails**
- [ ] **Step 7: Create `.dockerignore` ignoring virtual environments, caches, coverage, build outputs, and `.env`**
- [ ] **Step 8: Commit Task 1 changes**

---

### Task 2: Agent Guidelines & Quality Checklists (`.agents/`)

**Files:**
- Create: `.agents/README.md`
- Create: `.agents/checklists/clean-architecture-review.md`
- Create: `.agents/checklists/agent-safety-review.md`
- Create: `.agents/checklists/open-source-readiness.md`
- Create: `.agents/checklists/frontend-design-review.md`
- Create: `.agents/checklists/product-architecture-review.md`

- [ ] **Step 1: Create `.agents/README.md` explaining agent governance in this repository**
- [ ] **Step 2: Create `.agents/checklists/clean-architecture-review.md`**
- [ ] **Step 3: Create `.agents/checklists/agent-safety-review.md`**
- [ ] **Step 4: Create `.agents/checklists/open-source-readiness.md`**
- [ ] **Step 5: Create `.agents/checklists/frontend-design-review.md`**
- [ ] **Step 6: Create `.agents/checklists/product-architecture-review.md`**
- [ ] **Step 7: Commit Task 2 changes**

---

### Task 3: GitHub Templates & CI Workflows (`.github/`)

**Files:**
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/security.yml`

- [ ] **Step 1: Create `.github/PULL_REQUEST_TEMPLATE.md` with PR checklist and test verification requirements**
- [ ] **Step 2: Create `.github/ISSUE_TEMPLATE/bug_report.yml` and `feature_request.yml`**
- [ ] **Step 3: Create `.github/workflows/ci.yml` for backend tests (`pytest`) and Flutter tests (`flutter test` + `analyze`)**
- [ ] **Step 4: Create `.github/workflows/security.yml` for secret scanning and dependency audits**
- [ ] **Step 5: Commit Task 3 changes**

---

### Task 4: Infrastructure Organization (`infra/`)

**Files:**
- Create: `infra/docker/compose.yaml` (canonical link / copy)
- Create: `infra/docker/compose.integration.yaml`
- Create: `infra/docker/README.md`
- Create: `infra/deploy/compose.production.yml`
- Create: `infra/deploy/README.md`
- Create: `infra/backups/.gitignore`
- Create: `infra/backups/README.md`

- [ ] **Step 1: Set up `infra/docker/` with compose topologies and service documentation**
- [ ] **Step 2: Set up `infra/deploy/` with production deployment guidance and compose template**
- [ ] **Step 3: Set up `infra/backups/` with `.gitignore` for backup dumps and backup documentation**
- [ ] **Step 4: Commit Task 4 changes**

---

### Task 5: Scripts Organization (`scripts/{audit,dev,ops}/`)

**Files:**
- Create: `scripts/audit/check-no-secrets.sh`
- Create: `scripts/audit/check-no-hardcoded-config.sh`
- Create: `scripts/audit/check-compose.sh`
- Create: `scripts/audit/env-example-check.sh`
- Create: `scripts/dev/test-knowledge-integration.sh`
- Create: `scripts/dev/build-full-knowledge-graph.sh`
- Create: `scripts/dev/test-tutor-queries.sh`
- Create: `scripts/ops/export-seed.sh`
- Create: `scripts/ops/import-seed.sh`
- Create: `scripts/ops/backup-db.sh`
- Create: `scripts/ops/restore-db.sh`

- [ ] **Step 1: Organize audit scripts in `scripts/audit/`**
- [ ] **Step 2: Organize development & testing scripts in `scripts/dev/`**
- [ ] **Step 3: Organize operations & backup scripts in `scripts/ops/`**
- [ ] **Step 4: Ensure all script files have execution permissions (`chmod +x`)**
- [ ] **Step 5: Commit Task 5 changes**

---

### Task 6: Root Developer Workflow (`Makefile`)

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Implement `Makefile` with targets: `help`, `up`, `down`, `logs`, `test`, `test-backend`, `test-mobile`, `analyze`, `lint`, `seed`, `audit`**
- [ ] **Step 2: Test `make help`, `make test-backend`, and `make test-mobile` to verify targets**
- [ ] **Step 3: Commit Task 6 changes**

---

### Task 7: Architectural Documentation & README Standardization (`docs/`, `README.md`)

**Files:**
- Create: `docs/project-structure.md`
- Create: `docs/dependencies.md`
- Create: `docs/architecture/system-overview.md`
- Move/Adapt: `brainstorm_english7_graphrag_idea.md` -> `docs/architecture/graphrag-ideation.md`
- Update: `README.md`

- [ ] **Step 1: Create `docs/project-structure.md` detailing the standardized monorepo layout**
- [ ] **Step 2: Create `docs/dependencies.md` detailing Python, Flutter, and Docker dependencies**
- [ ] **Step 3: Create `docs/architecture/system-overview.md` with system baseline and GraphRAG diagrams**
- [ ] **Step 4: Relocate `brainstorm_english7_graphrag_idea.md` to `docs/architecture/graphrag-ideation.md`**
- [ ] **Step 5: Update `README.md` with badges, status, architecture links, Makefile commands, and quickstart guide**
- [ ] **Step 6: Commit Task 7 changes**

---

### Task 8: Full Verification Gate

- [ ] **Step 1: Run `make test-backend` and verify 163 tests pass**
- [ ] **Step 2: Run `make test-mobile` and verify 33 tests pass**
- [ ] **Step 3: Run `make analyze` and verify 0 errors, 0 warnings**
- [ ] **Step 4: Run `git status` and verify repository cleanliness**
- [ ] **Step 5: Push `main` to origin**
