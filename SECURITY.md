<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Security Policy

## Supported Versions

Security reports for the `main` branch and active development releases are accepted and prioritized.

## Reporting a Vulnerability

Do not create a public GitHub issue for security vulnerabilities or credential disclosures.

Please report vulnerabilities privately through GitHub Security Advisories or by contacting the repository maintainers.

## Sensitive Data Guidelines

- Never commit secrets, real passwords, private API keys, production tokens, or student personal identifiers to the repository.
- Ensure all test suites use mocks or local docker services.
- Never commit `.env` files containing live credentials. Use `.env.example` as the canonical template.
