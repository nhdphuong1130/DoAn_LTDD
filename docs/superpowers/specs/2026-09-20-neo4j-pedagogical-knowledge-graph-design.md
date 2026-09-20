# Superseded: Neo4j Pedagogical Knowledge Graph & Weighted GraphRAG

- **Date:** 2026-09-20
- **Status:** Superseded
- **Replacement:** [`docs/plans/2026-09-20-evidence-first-adaptive-knowledge-graph-design.md`](../../plans/2026-09-20-evidence-first-adaptive-knowledge-graph-design.md)

This initial specification has been replaced after review of the running SQL
Server and Neo4j data, the current retrieval implementation, and the desired
adaptive-learning workflow. Git history retains the original specification.

The replacement design makes the following requirements explicit:

- SQL Server remains the source of truth and Neo4j remains rebuildable;
- every pedagogical assertion requires provenance and review status;
- concept retrieval must resolve to verified textbook evidence;
- quiz results update an explainable student mastery model;
- remediation is proposed to the student before a learning plan is created;
- graph builds are versioned, validated, reversible, and isolated from tests;
- success is measured against a vector-only baseline.
