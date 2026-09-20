# Evidence-First Adaptive Knowledge Graph Design

- **Date:** 2026-09-20
- **Status:** Approved design
- **Scope:** English 7 Global Success, Units 1–12 and Reviews 1–4
- **Supersedes:** `docs/superpowers/specs/2026-09-20-neo4j-pedagogical-knowledge-graph-design.md`
- **Target:** Tutor retrieval, grounded quiz generation, learning diagnosis,
  and student-confirmed remediation

## 1. Purpose

The knowledge graph must support one closed learning loop:

```text
Learn textbook content
→ ask the grounded tutor
→ take a concept-aligned quiz
→ diagnose missing knowledge
→ propose a remediation plan
→ student accepts or rejects the proposal
→ practise and reassess
→ update mastery
```

The graph is successful only when it improves answer grounding, lesson
retrieval, quiz quality, and explainable diagnosis. Increasing node or
relationship counts is not itself a success criterion.

## 2. Verified Current State

Read-only checks against the running services on 2026-09-20 found:

| Store | Verified state |
|---|---|
| SQL Server | 16 units, 92 sections, 458 activities |
| SQL Server | 458 source fragments, all marked verified |
| SQL Server | 88 audio tracks and 88 media assets |
| Neo4j | 42 SourceFragments and only structural relationships |
| Neo4j | 18 two-dimensional and 24 384-dimensional embeddings |
| Neo4j | one online two-dimensional test vector index |
| Neo4j | one uniqueness constraint, on `SourceFragment.sql_id` |

Neo4j also contains more `Textbook` and `Unit` nodes than expected for the 42
fragments. The migration must therefore treat the current graph as mixed
runtime/test data rather than as a clean production baseline.

## 3. Goals and Non-Goals

### Goals

1. Retrieve the correct verified textbook evidence for Vietnamese and English
   tutor queries.
2. Generate quizzes from explicit concept, skill, difficulty, and source
   blueprints.
3. Diagnose weak concepts from multiple assessment observations.
4. Traverse prerequisites and common mistakes to recommend exact lessons and
   activities.
5. Explain every diagnosis and recommendation using stored evidence.
6. Rebuild, validate, activate, and roll back graph versions safely.

### Non-goals for this iteration

- Fully autonomous learning plans that students cannot review.
- A separate graph per student.
- Replacing SQL Server with Neo4j for transactional business data.
- Letting an LLM assign mastery or create facts without review.
- Global graph summaries, community detection, or a separate vector database.

## 4. Architectural Boundaries

```text
SQL Server — system of record
├── textbook content and review state
├── questions, answers, attempts, and scoring
├── per-student mastery observations
├── remediation proposals and accepted plans
└── audit history
             │
             ▼ verified-data synchronization
Neo4j — rebuildable reasoning and retrieval projection
├── textbook hierarchy
├── pedagogical concepts and prerequisites
├── question-to-concept mappings
├── concept-to-evidence mappings
└── concept-to-lesson and common-mistake paths
             │
       ┌─────┴──────────┐
       ▼                ▼
Tutor Retrieval   Learning Diagnosis
       │                │
       └──────┬─────────┘
              ▼
     Remediation Recommender
```

SQL Server is authoritative. Neo4j stores a derived, versioned projection and
can be discarded and rebuilt. Per-student attempts and mastery stay in SQL
Server. Neo4j is queried with the student's weak concept IDs when prerequisite
or remediation traversal is needed.

## 5. Graph Ontology

### 5.1 Structural nodes

```text
(:Textbook)-[:HAS_UNIT]->(:Unit)
(:Unit)-[:HAS_SECTION]->(:Section)
(:Section)-[:HAS_ACTIVITY]->(:Activity)
(:Activity)-[:HAS_SOURCE]->(:SourceFragment)
```

All structural nodes use their stable SQL UUID as `sql_id`. A `Unit` also has
`unit_kind`, `display_order`, and optional `review_cycle`. Legacy values such as
31, 61, 91, and 121 remain import identifiers only; retrieval must not infer
review semantics from those numbers.

### 5.2 Pedagogical nodes

Every pedagogical node has `:KnowledgeConcept` and one subtype label:

| Subtype | Purpose |
|---|---|
| `GrammarConcept` | A reusable grammar rule or construction |
| `VocabularySense` | One meaning of a lemma in a part of speech |
| `PronunciationFeature` | Phoneme, ending, stress, or intonation |
| `Topic` | A communicative theme |
| `Skill` | Listening, speaking, reading, or writing |

A concept exists independently from a unit. For example, Present Simple is one
concept that can be introduced, practised, assessed, and reviewed in different
parts of the curriculum.

Required common properties are:

```text
concept_id
canonical_name
description_en
description_vi
concept_text
ontology_version
review_status
```

`VocabularySense` additionally stores `lemma`, `normalized_form`, `pos`, `ipa`,
`meaning_vi`, and lexical variants. `PronunciationFeature.feature_type` is one
of `PHONEME`, `ENDING`, `WORD_STRESS`, or `INTONATION`.

### 5.3 Assessment nodes

```text
(:QuizQuestion)
(:CommonMistake)
```

Only validated and released questions are projected into Neo4j. Attempts and
answers remain in SQL Server.

### 5.4 Semantic relationships

```text
(Activity|SourceFragment)-[:TEACHES]->(KnowledgeConcept)
(Activity|SourceFragment)-[:PRACTICES]->(KnowledgeConcept)
(SourceFragment)-[:EXPLAINS]->(KnowledgeConcept)
(Unit)-[:INTRODUCES]->(KnowledgeConcept)
(Unit {unit_kind: 'REVIEW'})-[:REVIEWS]->(KnowledgeConcept)
(QuizQuestion)-[:ASSESSES]->(KnowledgeConcept)
(QuizQuestion)-[:SUPPORTED_BY]->(SourceFragment)
(KnowledgeConcept)-[:PREREQUISITE_OF]->(KnowledgeConcept)
(KnowledgeConcept)-[:HAS_COMMON_MISTAKE]->(CommonMistake)
```

Review units link to the concepts actually reviewed, not merely to three whole
units. A question has one primary assessed concept and may have lower-weighted
secondary concepts.

## 6. Provenance and Review Policy

Every semantic assertion stores:

```text
role_weight
confidence
review_status
source_fragment_id or evidence_reference
created_by
model_version
ontology_version
reviewed_by
reviewed_at
```

Only `VERIFIED` concepts and relationships participate in tutor retrieval,
quiz generation, diagnosis, or remediation. AI-extracted assertions enter as
`PROPOSED`. They do not become facts until reviewed.

Relationship weight represents pedagogical role, not truth. `confidence`
represents confidence in the assertion, while `review_status` controls whether
the assertion may be used. These fields must not be collapsed into one score.

## 7. Embedding Lifecycle

The same model and preprocessing pipeline must be used at indexing and query
time. The model is selected only after benchmarking English and Vietnamese
queries. The initial comparison includes the proposed MiniLM model and at least
one multilingual 384-dimensional candidate.

Each embedded node stores or inherits from its graph build:

```text
embedding_model
embedding_model_version
embedding_dimensions
embedding_input_hash
embedded_at
```

`SourceFragment` embedding input uses normalized textbook text plus controlled
hierarchy metadata. `KnowledgeConcept` input uses canonical name, bilingual
description, aliases, and examples that have verified sources.

Changing model, preprocessing, or dimensions requires a new graph build and
new vector indexes. Model artifacts must be preloaded into the deployment
image or cache. Offline runtime does not imply that the build has no external
artifact dependency.

## 8. Evidence-First Tutor Retrieval

### 8.1 Flow

```text
Query plus current lesson context
→ normalize language and parse explicit Unit/Review scope
→ embed query
→ fragment vector search and concept vector search
→ resolve every concept candidate to verified evidence fragments
→ expand only through approved relationship types, at most two hops
→ create three deterministic rankings
→ weighted reciprocal-rank fusion
→ evidence diversity and duplicate removal
→ closed context assembly
→ LLM structured answer with source_fragment_ids
→ backend citation validation
```

The three rankings are:

1. direct fragment vector ranking;
2. concept-to-evidence ranking;
3. graph expansion ranking.

For a graph path:

```text
path_score = seed_score
             × product(role_weight × confidence for semantic edges)
             × hop_decay^(hop_count - 1)
```

The best valid path per evidence fragment is retained. Structural edges do not
add pedagogical importance. Traversal uses an explicit relationship and node
allowlist; it never uses an unrestricted `[*1..N]` query.

Final fusion is rank-based:

```text
RRF(item) = Σ source_weight / (rrf_constant + rank_in_source)
```

Weights, top-k values, thresholds, candidate oversampling, and hop decay are
configuration values calibrated on the evaluation set.

### 8.2 Grounding invariants

- The final context contains only verified `SourceFragment` nodes.
- A concept without verified evidence cannot enter the context.
- Explicit Unit/Review scope is applied before final ranking.
- Citations include fragment ID, textbook version, Unit, Section, Activity,
  printed page, and PDF page.
- An LLM citation not present in the supplied context invalidates the response.
- With insufficient evidence, the tutor abstains instead of using unsupported
  general knowledge.

## 9. Grounded Quiz Generation

The backend creates a `QuizBlueprint` before calling an LLM:

```text
scope
→ concepts and coverage weights
→ skills
→ difficulty distribution
→ question types
→ verified supporting fragments
```

The LLM writes within the blueprint and supplied evidence. It does not choose
the syllabus. A validator rejects questions that are outside scope, unsupported,
ambiguous, duplicated, incorrectly keyed, inappropriate in difficulty, or that
expose protected listening transcripts.

After validation and release, SQL Server stores the immutable question version.
Neo4j receives `ASSESSES` and `SUPPORTED_BY` relationships. Editing a released
question creates a new version so scoring and later diagnosis remain
reproducible.

## 10. Student Mastery and Diagnosis

### 10.1 Observation model

For each answered question, SQL Server records:

```text
student_id, attempt_id, question_version_id
primary_concept_id, secondary_concept_ids
correct, selected_answer, difficulty
hint_used, attempt_number, answered_at
```

The MVP uses a deterministic weighted-evidence model. Each observation receives
a configurable weight based on concept contribution, question difficulty, hint
use, and recency. For a concept:

```text
mastery_score = Σ(observation_weight × correctness) / Σ(observation_weight)
confidence = min(1, effective_evidence / required_evidence)
```

The stored result includes `evidence_count`, `effective_evidence`,
`last_assessed_at`, and one state:

```text
UNASSESSED | DEVELOPING | NEEDS_REVIEW | MASTERED
```

No weak/mastered conclusion is made below the configured evidence threshold.
Thresholds are initially expert-defined, then calibrated from real outcomes.

### 10.2 Root-cause diagnosis

For every sufficiently supported weak concept, the service:

1. identifies wrong questions and selected distractors;
2. maps reviewed distractors to `CommonMistake` nodes;
3. traverses verified prerequisites;
4. checks the student's SQL mastery for those prerequisites;
5. distinguishes a prerequisite gap from a target-concept gap;
6. finds the closest verified explanations and practice activities.

An LLM may phrase the explanation, but it cannot decide mastery or invent the
root cause. If a distractor has no reviewed mistake mapping, the system reports
only the observed concept weakness.

## 11. Remediation Proposal

A recommendation is proposed before a learning plan is created. It contains:

```text
weak concept and confidence
supporting question evidence
identified prerequisite or common mistake
exact Unit / Section / Activity to review
verified explanation fragments
practice activity
five-question micro-quiz
recommended reassessment time
human-readable reason for every selection
```

The student may accept, reject, or defer it. Only acceptance creates an active
plan. Completion of the review and micro-quiz adds new observations and updates
mastery. The next action is selected deterministically:

- prerequisite still weak: continue prerequisite remediation;
- prerequisite strong but target weak: practise target concept;
- target meets mastery and evidence thresholds: complete the concept;
- insufficient evidence: request another diagnostic micro-quiz.

Student choices and outcomes are retained for later recommendation evaluation.

## 12. Versioned Graph Build and Migration

Each build creates a `GraphBuild` record with:

```text
build_id, source_checksum, ontology_version
embedding model/version/dimensions
start/end timestamps, status
expected and actual counts
validation report
```

Statuses are `BUILDING`, `VALIDATED`, `ACTIVE`, `FAILED`, and `RETIRED`.

Build procedure:

1. acquire a singleton build lock;
2. read one consistent snapshot of verified SQL data;
3. build nodes and relationships in batches under a new `build_id`;
4. create version-specific vector indexes;
5. wait for all indexes to become online;
6. reconcile counts, identities, stale data, and orphan nodes;
7. run retrieval and graph smoke tests;
8. mark the build validated;
9. atomically change the active build metadata used by runtime;
10. retain the previous build for rollback, then retire it after a configured
    safety period.

Versioned graph identities use `(sql_id, build_id)` or `(concept_id, build_id)`.
Runtime queries always constrain `build_id` and use the matching index name.
Re-running a build with the same source checksum must produce the same logical
graph. `MERGE` alone is not considered reconciliation.

The first migration builds from SQL Server rather than attempting to repair the
mixed two-dimensional/384-dimensional graph in place. Integration tests use a
separate Neo4j container or database and never target runtime data.

## 13. Failure Handling

- Embedding failures are retried with bounded backoff. Persistent failure marks
  the entire candidate build failed; a partial build is never activated.
- A vector index must be online before validation and cutover.
- Invalid dimensions, missing evidence, duplicate identities, or orphaned
  structural nodes fail validation.
- Neo4j unavailability never triggers an ungrounded tutor answer.
- Released quizzes continue from immutable SQL data while Neo4j is unavailable.
- Invalid LLM output or citations are rejected and may be regenerated within a
  bounded retry limit.
- Diagnosis with insufficient evidence returns `UNASSESSED` or requests more
  questions rather than declaring weakness.
- Every build, retrieval failure, abstention, quiz rejection, and recommendation
  outcome is observable with a correlation ID and non-sensitive metadata.

## 14. Configuration

All deployment-dependent values are externally configured and validated at
startup:

```text
active graph build/index names
embedding model, cache, dimensions, and batch size
fragment and concept candidate counts
minimum vector/evidence confidence
allowed relationship types and maximum graph depth
path hop decay and RRF source weights
maximum context fragments/tokens
mastery evidence threshold and state thresholds
question difficulty, hint, and recency weights
reassessment intervals and retry limits
```

The design document does not prescribe unbenchmarked latency or similarity
thresholds as facts.

## 15. Verification and Acceptance

### 15.1 Evaluation set

Create a locked, versioned dataset with at least 10–15 queries per Unit/Review,
covering Vietnamese and English, explicit and implicit scope, grammar,
vocabulary, pronunciation, skills, ambiguity, prerequisites, and out-of-scope
questions. Expected results specify acceptable concepts and source fragments,
not only pages.

### 15.2 Tutor acceptance

| Metric | Initial gate |
|---|---:|
| Citation precision | 100% |
| Verified-source rate | 100% |
| Unit/Section accuracy | at least 90% |
| Recall@5 | at least 85% |
| Out-of-scope abstention | at least 90% |

Hybrid retrieval must outperform a locked vector-only baseline. Measure p50 and
p95 retrieval latency on the deployment CPU; do not infer it from model claims.

### 15.3 Quiz acceptance

- 100% of released questions have verified support.
- 100% match their blueprint scope and primary concept.
- Answer validation is deterministic and reproducible.
- Protected transcripts are absent from active tests.
- A reviewed sample meets agreed correctness, difficulty, and distractor
  quality thresholds.

### 15.4 Diagnosis and remediation acceptance

- Insufficient evidence never produces a weak/mastered classification.
- The same answer history produces the same mastery result.
- A weak prerequisite is recommended before its dependent concept.
- Only reviewed distractors produce named common-mistake diagnoses.
- Accepted plans point to existing verified lessons and activities.
- Micro-quiz completion updates observations, mastery, and next action.

### 15.5 Test layers

1. Unit tests for scoring, path scoring, fusion, filtering, and state changes.
2. Contract tests for SQL-to-graph projection and schema invariants.
3. Neo4j integration tests for constraints, versioned indexes, traversal, and
   rollback in isolated infrastructure.
4. End-to-end tests from quiz submission to remediation proposal and reassessment.
5. Evaluation tests comparing vector-only and hybrid retrieval.
6. Pilot monitoring for proposal acceptance and reassessment improvement.

## 16. Delivery Phases

### Phase 1 — Trustworthy graph foundation

Implement reviewed concepts, provenance, versioned builds, multilingual model
evaluation, verified evidence retrieval, and migration from the current graph.

### Phase 2 — Grounded tutor and quiz

Deploy hybrid tutor retrieval, closed-context citation validation, blueprint-led
quiz generation, and question-to-concept mappings.

### Phase 3 — Diagnosis and remediation

Implement mastery observations, prerequisite root-cause analysis, explained
proposals, student confirmation, micro-quizzes, and reassessment.

Each phase has its own acceptance gate and can be rolled back independently.
