<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Agent Safety & AI Grounding Review

Use this checklist to verify pedagogical safety, LLM response grounding, and secret isolation.

## Grounded Pedagogical Safety

- [ ] **Mandatory Citation**: Every tutor answer citing textbook concepts must provide source evidence (`[Unit X, Page Y, Activity Z]`).
- [ ] **Anti-Hallucination**: The system prompt instructs the tutor to reject answering out-of-scope general trivia or unverified grammar rules.
- [ ] **Curriculum Constraint**: Concept retrieval queries are constrained to Grade 7 syllabus scope.
- [ ] **RRF & Threshold Filtering**: Low-relevance retrieval results (< minimum similarity threshold) are pruned before context assembly.

## Credential & Runtime Security

- [ ] **No Hardcoded Keys**: No API keys (OpenRouter, JWT secrets, passwords) exist in code, tests, or documentation.
- [ ] **Secret Value Masking**: Secret settings use Pydantic `SecretStr` to prevent accidental logging.
- [ ] **Role-Based Authorization**: Endpoints protecting student personal data enforce authentication via JWT dependencies.
- [ ] **Input Sanitization**: User-submitted queries and filenames are sanitized against directory traversal and Cypher/SQL injection.
