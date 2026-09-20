<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Contributing Guidelines

The English 7 Grounded Learning Platform is an open-source, grounded pedagogical learning platform built for Vietnamese Grade 7 English learners. Contributions must maintain pedagogical correctness, grounded citations, and clean architecture standards.

## Branches

Use task-scoped branches named:

```text
<type>/<short-description>
```

Valid types: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`.
Examples:
- `feat/personal-profile`
- `feat/neo4j-pedagogical-graphrag`
- `fix/media-stream-fallback`

## Commits

Use Conventional Commits:

```text
<type>(<scope>): <imperative summary>
```

Examples:
- `feat(curriculum): implement semester 2 lessons, audio player, and quiz flows`
- `fix(backend): resolve media router database fallback in unit tests`
- `docs: standardize repository structure to OLP 2026 guidelines`

Keep commits atomic. Update tests, documentation, and `CHANGELOG.md` in the same commit as the code change.

## Verification Gates

Before submitting a pull request or pushing code, verify all gates pass:

```bash
# Run all tests (backend and mobile)
make test

# Run static analysis
make analyze

# Check audit scripts
make audit
```

## Pull Requests

PRs should include:
1. Summary of changes and pedagogical justification.
2. Evidence of test passes (backend pytest output and mobile flutter test output).
3. Updated documentation and changelog entries.
