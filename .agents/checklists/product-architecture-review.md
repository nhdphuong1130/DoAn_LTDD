<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Product Architecture Review

Use this checklist to ensure features align with curriculum learning objectives and the grounded GraphRAG architecture.

## Curriculum Scope Alignment

- [ ] **Curriculum Completeness**: Content covers both Semester 1 (Units 1-6 + Review 1-2) and Semester 2 (Units 7-12 + Review 3-4).
- [ ] **Granular Units**: Pedagogical concepts are classified by type (`Topic`, `GrammarRule`, `Vocabulary`, `PronunciationSound`).
- [ ] **Knowledge Graph Relationships**: Relationships between fragments and concepts use standard edge labels (`TEACHES`, `EXPLAINS`, `PRACTICES`, `PREREQUISITE_OF`).

## Knowledge Graph Lifecycle

- [ ] **Build Versioning**: Knowledge builds can be populated in an isolated build namespace without corrupting production queries.
- [ ] **Verification Pre-flight**: Vector dimensions and graph connectivity are verified before active promotion.
- [ ] **Dual Vector Indexes**: Graph supports fast retrieval for both unstructured passages (`SourceFragment`) and semantic concepts (`KnowledgeConcept`).
