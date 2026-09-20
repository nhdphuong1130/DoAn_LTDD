# Design Specification: Neo4j Pedagogical Knowledge Graph & Weighted GraphRAG

- **Date:** 2026-09-20
- **Status:** Approved
- **Scope:** Complete curriculum (Units 1–12 + Reviews 1–4, 16 units total, 92 sections, 458 activities/fragments)
- **Target Components:** Neo4j Knowledge Graph, FastEmbed Offline Vectorizer, Weighted GraphRAG Retrieval Service, AI Tutor & Quiz Integration

---

## 1. Overview & Objectives

### 1.1 Context
The English 7 (Global Success) mobile learning application has complete authentic curriculum data seeded in SQL Server and MinIO:
- 16 units (12 regular units + 4 review units)
- 92 sections
- 458 activities
- 458 source fragments (100% verified authentic textbook excerpts with page references)
- 88 audio tracks and textbook cropped images

Previously, the Neo4j database only contained a basic physical hierarchy (`Textbook -> Unit -> Section -> Activity -> SourceFragment`) for 42 early fragments, with dummy 2-dimensional test vectors, no semantic or pedagogical entity nodes (Grammar, Vocabulary, Topics, Pronunciation), unweighted relations, and retrieval restricted to Units 1 and 2.

### 1.2 Core Objectives
1. **Rich Pedagogical Knowledge Graph**: Model the textbook curriculum into a Dual-Tier Graph in Neo4j comprising both the physical book structure and a domain-specific pedagogical ontology (Grammar Rules, Vocabulary, Topics, Pronunciation Sounds, Skills).
2. **Weighted Semantic Relationships**: Establish pedagogical relations (`TEACHES: 1.0`, `EXPLAINS: 0.9`, `REVIEWS: 0.8`, `PREREQUISITE_OF: 0.7`, `PRACTICES: 0.6`, `APPEARS_IN: 0.5`) allowing graph traversal to prioritize core theoretical explanations over exercise fragments.
3. **Local FastEmbed 384-dimensional Vector Pipeline**: Vectorize all 458 SourceFragments and key pedagogical entities offline using `all-MiniLM-L6-v2` via FastEmbed/ONNX Runtime on CPU (matching system configuration of 384 dimensions, zero API cost, zero external dependency, ~10ms latency).
4. **Weighted GraphRAG Retrieval**: Upgrade the `RetrievalService` to perform dual vector matching, weighted graph traversal, and weighted Reciprocal Rank Fusion (RRF), supporting all 16 units.
5. **Grounded AI Tutor Context**: Provide structured, explainable context with textbook citations to the AI Tutor to guide students accurately.

---

## 2. Two-Tier Knowledge Graph Schema

### 2.1 Tier 1: Physical Curriculum Hierarchy (Structural Subgraph)
Preserves the exact structural hierarchy of the textbook for page and activity referencing:

```text
(:Textbook {sql_id, title, grade: 7})
   │
   ├──[:HAS_UNIT]──► (:Unit {sql_id, number, title, is_review: boolean})
                        │
                        ├──[:HAS_SECTION]──► (:Section {sql_id, title, section_type, position})
                                                │
                                                ├──[:HAS_ACTIVITY]──► (:Activity {sql_id, number, activity_type, instruction})
                                                                        │
                                                                        └──[:HAS_SOURCE]──► (:SourceFragment {sql_id, text, pdf_page, printed_page, embedding, verified})
```

### 2.2 Tier 2: Pedagogical Semantic Ontology (Knowledge Subgraph)
Specialized pedagogical nodes representing English language knowledge components:

1. **`(:Topic {id, name, description, unit_number})`**
   - Represents the central communicative theme of each unit (e.g., *Hobbies*, *Healthy Living*, *Community Service*, *Music & Arts*, *Food & Drink*, *School Visit*, *Traffic*, *Films*, *Festivals*, *Energy Sources*, *Future Transport*, *English-Speaking Countries*).

2. **`(:GrammarRule {id, name, formula, explanation_vi, examples, unit_number})`**
   - Core grammatical structures taught in *A Closer Look 2* and review sections:
     - Unit 1: Present Simple (Thì hiện tại đơn)
     - Unit 2: Simple Sentences & Compound Sentences with coordinators (and, or, but, so)
     - Unit 3: Past Simple (Thì quá khứ đơn)
     - Unit 4: Comparisons (*like, different from, (not) as ... as*)
     - Unit 5: Countable / Uncountable nouns, Quantifiers (*some, any, how much, how many*)
     - Unit 6: Prepositions of place & time (*at, in, on*)
     - Unit 7: "It" indicating distance; Connectors of contrast (*although, though, however*)
     - Unit 8: Connectors of contrast; Adjectives ending in *-ed* and *-ing*
     - Unit 9: Yes/No Questions & Wh-Questions in present and past
     - Unit 10: Present Continuous for future arrangements; Future Simple with will
     - Unit 11: Future Simple passive & Modal verbs for future transport
     - Unit 12: Articles (*a, an, the, zero article*)

3. **`(:Vocabulary {id, word, ipa, pos, meaning_vi, topic, unit_number})`**
   - Curated thematic vocabulary extracted from *Getting Started*, *A Closer Look 1*, and glossary of each unit.

4. **`(:PronunciationSound {id, symbol, ipa, sound_type, example_words, unit_number})`**
   - Target phonetic sounds from *A Closer Look 1* pronunciation activities:
     - Unit 1: `/ə/` and `/ɜː/`
     - Unit 2: `/f/` and `/v/`
     - Unit 3: `/t/`, `/d/`, and `/ɪd/` (past tense -ed endings)
     - Unit 4: `/ʃ/` and `/ʒ/`
     - Unit 5: `/ɒ/` and `/ɔː/`
     - Unit 6: `/tʃ/` and `/dʒ/`
     - Unit 7: `/e/` and `/eɪ/`
     - Unit 8: `/ɪə/` and `/eə/`
     - Unit 9: Stress in two-syllable words
     - Unit 10: Stress in two-syllable words (verbs & nouns)
     - Unit 11: Intonation in Yes/No questions and statements
     - Unit 12: Falling intonation for statements and wh-questions

5. **`(:Skill {id, name, category})`**
   - Skills: *Listening*, *Speaking*, *Reading*, *Writing*.

All pedagogical nodes also carry a composite label `:KnowledgeConcept` for unified vector and graph queries.

---

## 3. Weighted Relationship Matrix

Each relationship in the knowledge graph is assigned an explicit `weight` property (0.0 to 1.0) defining its pedagogical centrality:

| Relationship | Source Label | Target Label | Weight | Description |
|---|---|---|---|---|
| `TEACHES` | `Activity / SourceFragment` | `GrammarRule / PronunciationSound` | **1.0** | Core theory presentation: Remember boxes, grammar explanations, pronunciation tables. Highest retrieval priority. |
| `EXPLAINS` | `Activity / SourceFragment` | `Vocabulary` | **0.9** | Vocabulary definitions, glossary entries, meaning explanations. |
| `REVIEWS` | `Unit (Review)` | `Unit (Prior Units)` | **0.8** | Review units revisiting concepts from preceding units (e.g., Review 1 -> Units 1, 2, 3). |
| `PREREQUISITE_OF` | `GrammarRule` | `GrammarRule` | **0.7** | Foundational grammar required for advanced grammar (e.g., Present Simple -> Future Simple). |
| `PRACTICES` | `Activity / SourceFragment` | `GrammarRule / Vocabulary` | **0.6** | Practice exercises, fill-in-the-blanks, matching, comprehension questions. |
| `APPEARS_IN` | `Vocabulary / GrammarRule` | `Topic / SourceFragment` | **0.5** | Real-world usage in dialogue, reading passages, or thematic topics. |

---

## 4. Local FastEmbed 384-dimensional Vector Pipeline

### 4.1 Embedding Specifications
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Output Dimensions**: 384 (float32 array)
- **Distance Metric**: Cosine similarity
- **Engine**: `fastembed` (Python package powered by ONNX Runtime)
- **Execution Target**: CPU (portable, offline, fast, zero GPU dependency)
- **Inference Speed**: ~10ms per query, batch throughput >100 fragments/sec on standard CPU.

### 4.2 Neo4j Vector Indexes
The system creates and manages two vector indexes in Neo4j:

1. `source_fragment_embedding`:
   ```cypher
   CREATE VECTOR INDEX source_fragment_embedding IF NOT EXISTS
   FOR (f:SourceFragment) ON (f.embedding)
   OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}
   ```

2. `knowledge_concept_embedding`:
   ```cypher
   CREATE VECTOR INDEX knowledge_concept_embedding IF NOT EXISTS
   FOR (k:KnowledgeConcept) ON (k.embedding)
   OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}
   ```

---

## 5. Weighted GraphRAG Retrieval Algorithm

### 5.1 Retrieval Flow
```
Student Query (text)
        │
        ▼
[1] Embed query with FastEmbed (384d vector)
        │
   ┌────┴───────────────────────────┐
   ▼                                ▼
[2A] Vector Search SourceFragments   [2B] Vector Search KnowledgeConcepts
     (Top-K=8, min_score=0.60)           (Top-K=4, min_score=0.60)
   └────┬───────────────────────────┘
        │
        ▼
[3] Weighted Graph Expansion (Cypher)
    Traverse from seeds up to depth=2 using weighted relationships:
    - Base weight = r.weight (1.0 for TEACHES, 0.9 for EXPLAINS, 0.6 for PRACTICES...)
    - Hop decay = 0.8 ^ (hop - 1)
    - Effective Graph Score = max(r.weight * hop_decay)
        │
        ▼
[4] Weighted Reciprocal Rank Fusion (RRF)
    RRF_Score(item) = (1.0 / (60 + vector_rank)) + (1.2 * graph_score / (60 + graph_rank))
        │
        ▼
[5] Grounded Context Assembly
    Select top 6 fragments, extract deduplicated textbook citations:
    (unit_number, unit_title, section_title, printed_page, pdf_page)
```

### 5.2 Retrieval Constraints & Fallbacks
- `ENGLISH7_RETRIEVAL_ALLOWED_UNITS`: Expanded to `1,2,3,4,5,6,7,8,9,10,11,12,31,61,91,121` so all 16 units are retrievable.
- Explicit Unit Filter: If the student mentions a unit (e.g. "Unit 10" or "bài 10"), prioritize or filter results to that unit.
- Graceful Fallback: If graph expansion yields no neighbors, return pure vector search results with base confidence score.

---

## 6. Implementation Components

### 6.1 Backend Modules
1. `backend/src/english7/modules/knowledge/fastembed_service.py`:
   - Wraps `fastembed.TextEmbedding` with `sentence-transformers/all-MiniLM-L6-v2`.
   - Thread-safe singleton embedder with fallback.
2. `backend/src/english7/modules/knowledge/curriculum_ontology.py`:
   - Data structures and deterministic mapping of the 16 units into Topics, GrammarRules, Vocabulary, PronunciationSounds, and Skills with their corresponding textbook activities.
3. `backend/src/english7/modules/knowledge/neo4j_repository.py`:
   - Updated with methods for:
     - `ensure_schema()`: constraints and vector indexes for both fragments and concepts.
     - `upsert_pedagogical_nodes()`: inserts Topics, GrammarRules, Vocabulary, Pronunciation.
     - `upsert_weighted_relationships()`: creates `TEACHES`, `EXPLAINS`, `PRACTICES`, `PREREQUISITE_OF`, `REVIEWS`, `APPEARS_IN` with weights.
     - `weighted_graph_search()`: executes weighted Cypher traversal.
4. `backend/src/english7/modules/retrieval/service.py`:
   - Updates `RetrievalService` to incorporate concept matching and weighted RRF.
5. `backend/scripts/build_full_knowledge_graph.py`:
   - Comprehensive seeding script that:
     - Connects to SQL Server to fetch all 458 fragments.
     - Generates 384d embeddings for all fragments and pedagogical concepts via FastEmbed.
     - Builds both Tier 1 and Tier 2 graphs in Neo4j with full weighted relationships.
     - Verifies graph counts and index readiness.

---

## 7. Error Handling & Edge Cases

1. **FastEmbed Model Download / Cache**: Model weights are cached locally inside the container (`/app/cache/fastembed` or standard cache dir) so internet access is not required after initial run.
2. **Dimension Consistency**: Strict check ensuring `len(vector) == 384` before inserting into Neo4j.
3. **Database Consistency**: Scripts are idempotent (`MERGE` statements used for all nodes and relationships). Re-running the script updates weights and properties without duplicate nodes.
4. **Neo4j Constraints**: Unique constraints on `sql_id` for structural nodes and `id` for pedagogical concept nodes.

---

## 8. Verification Strategy

1. **Automated Unit & Integration Tests**:
   - `test_fastembed.py`: Verifies embedding output dimensions (384) and cosine similarity of similar vs dissimilar texts.
   - `test_neo4j_knowledge_graph.py`: Verifies node counts, label distributions, relationship types, and weight properties in Neo4j.
   - `test_weighted_retrieval.py`: Tests retrieval precision on sample queries across Semester 1 and Semester 2 topics:
     - Query: *"Khi nào dùng thì hiện tại đơn?"* -> Top candidate from Unit 1 / Unit 2 GrammarRule with `TEACHES` weight 1.0.
     - Query: *"What are renewable energy sources?"* -> Top candidate from Unit 10 Energy Sources.
     - Query: *"means of transport in the future"* -> Top candidate from Unit 11.
     - Query: *"capital of English-speaking countries"* -> Top candidate from Unit 12.
2. **Live Verification in Mobile App**:
   - Ask questions in the mobile Tutor chat screen and confirm that answer explanations contain authentic textbook citations with correct unit and page numbers.
