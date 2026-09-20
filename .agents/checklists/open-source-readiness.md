<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Open-Source Readiness (OLP 2026 Criteria)

Use this checklist to ensure the project meets national open-source competition criteria (Olympic Tin học / OLP).

## Licensing & Attribution

- [ ] Repository has an OSI-approved `LICENSE` file (Apache-2.0).
- [ ] Source files and scripts include SPDX headers.
- [ ] Third-party dependencies and assets (audio, fonts, images) are inventoried in `docs/dependencies.md`.

## Build from Source Quality

- [ ] The repository builds and runs cleanly from source on Linux and macOS/Windows.
- [ ] Setup documentation (`docs/setup-linux.md`, `docs/setup-windows.md`) is tested and up to date.
- [ ] `make test`, `make analyze`, and `make up` execute predictably without manual guesswork.

## Community & Governance

- [ ] `README.md` provides a concise project summary, architecture diagrams, and quickstart commands.
- [ ] `CONTRIBUTING.md` outlines pull request and commit conventions.
- [ ] `CODE_OF_CONDUCT.md` establishes community standards.
- [ ] `SECURITY.md` defines private vulnerability disclosure.
- [ ] `CHANGELOG.md` reflects version history and unreleased changes.
