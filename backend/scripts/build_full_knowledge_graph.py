import os
import sys
import time
from uuid import UUID
from neo4j import GraphDatabase
from sqlalchemy import text

from english7.core.settings import get_settings
from english7.db.session import get_engine
from english7.modules.knowledge.curriculum_ontology import get_curriculum_ontology
from english7.modules.knowledge.fastembed_service import FastEmbedService
from english7.modules.knowledge.neo4j_repository import Neo4jKnowledgeRepository


def main():
    print("=" * 70)
    print("🚀 STARTING FULL KNOWLEDGE GRAPH BUILD FOR TIẾNG ANH 7")
    print("=" * 70)
    start_time = time.time()

    settings = get_settings()
    engine = get_engine()

    # 1. Connect to SQL Server and fetch all verified fragments
    print("\n[1/5] Fetching verified fragments and textbook hierarchy from SQL Server...")
    query = text("""
        SELECT 
            sf.id AS fragment_id,
            sf.normalized_text,
            sf.pdf_page,
            sf.printed_page,
            a.id AS activity_id,
            a.number AS activity_number,
            a.activity_type,
            a.instruction AS activity_instruction,
            s.id AS section_id,
            s.title AS section_title,
            s.position AS section_position,
            s.section_type,
            u.id AS unit_id,
            u.number AS unit_number,
            u.title AS unit_title,
            tb.id AS textbook_id,
            tb.title AS textbook_title
        FROM source_fragments sf
        JOIN activities a ON sf.activity_id = a.id
        JOIN sections s ON a.section_id = s.id
        JOIN units u ON s.unit_id = u.id
        JOIN textbooks tb ON u.textbook_id = tb.id
        WHERE sf.review_status = 'verified' AND sf.is_published = 1
        ORDER BY u.number, s.position, a.number
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    print(f"  ✓ Fetched {len(rows)} verified fragments across all units.")
    if not rows:
        print("  ❌ No verified fragments found. Exiting.")
        sys.exit(1)

    # 2. Initialize FastEmbed embedder
    print("\n[2/5] Initializing FastEmbed Service (sentence-transformers/all-MiniLM-L6-v2, 384d)...")
    embedder = FastEmbedService()
    print("  ✓ Embedder ready.")

    # 3. Setup Neo4j connection and ensure schema
    print("\n[3/5] Connecting to Neo4j and establishing constraints & vector indexes...")
    neo4j_driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
    )
    repo = Neo4jKnowledgeRepository(
        neo4j_driver,
        vector_index_name=settings.neo4j_vector_index,
        embedding_dimensions=384,
        graph_result_limit=settings.retrieval_top_k,
    )

    with neo4j_driver.session() as session:
        existing_indexes = session.run("SHOW INDEXES").data()
        for idx in existing_indexes:
            if idx.get("type") == "VECTOR":
                try:
                    session.run(f"DROP INDEX {idx['name']} IF EXISTS").consume()
                    print(f"  ✓ Dropped existing vector index {idx['name']} for fresh recreation.")
                except Exception as e:
                    print(f"  Notice dropping index {idx.get('name')}: {e}")
        session.run("MATCH (f:SourceFragment) WHERE size(f.embedding) <> 384 DETACH DELETE f").consume()
        session.run("MATCH (a:Activity) WHERE NOT (a)-[:HAS_SOURCE]->() DETACH DELETE a").consume()
        session.run("MATCH (s:Section) WHERE NOT (s)-[:HAS_ACTIVITY]->() DETACH DELETE s").consume()

    repo.ensure_schema()
    print("  ✓ Schema constraints and dual 384d vector indexes ensured.")

    # 4. Ingest and embed physical textbook hierarchy into Neo4j
    print("\n[4/5] Embedding fragments and upserting textbook structural hierarchy...")
    batch_size = 50
    total_rows = len(rows)

    with neo4j_driver.session() as session:
        for i in range(0, total_rows, batch_size):
            batch = rows[i : i + batch_size]
            texts = [r.normalized_text for r in batch]
            embeddings = embedder.embed_batch(texts)

            for r, emb in zip(batch, embeddings):
                cypher = """
                MERGE (tb:Textbook {sql_id: $tb_id})
                SET tb.title = $tb_title
                MERGE (u:Unit {sql_id: $u_id})
                SET u.number = $u_number, u.title = $u_title, u.is_review = $is_review
                MERGE (s:Section {sql_id: $s_id})
                SET s.title = $s_title, s.position = $s_pos, s.section_type = $s_type
                MERGE (a:Activity {sql_id: $a_id})
                SET a.number = $a_number, a.activity_type = $a_type, a.instruction = $a_inst
                MERGE (f:SourceFragment {sql_id: $f_id})
                SET f.text = $f_text,
                    f.pdf_page = $f_pdf,
                    f.printed_page = $f_printed,
                    f.unit_number = $u_number,
                    f.embedding = $embedding,
                    f.verified = true,
                    f.hierarchy = [$tb_title, 'Unit ' + toString($u_number) + ': ' + $u_title, $s_title, $a_number]
                MERGE (tb)-[:HAS_UNIT]->(u)
                MERGE (u)-[:HAS_SECTION]->(s)
                MERGE (s)-[:HAS_ACTIVITY]->(a)
                MERGE (a)-[:HAS_SOURCE]->(f)
                """
                params = {
                    "tb_id": str(r.textbook_id),
                    "tb_title": r.textbook_title,
                    "u_id": str(r.unit_id),
                    "u_number": r.unit_number,
                    "u_title": r.unit_title,
                    "is_review": "review" in r.unit_title.lower(),
                    "s_id": str(r.section_id),
                    "s_title": r.section_title,
                    "s_pos": r.section_position,
                    "s_type": r.section_type,
                    "a_id": str(r.activity_id),
                    "a_number": str(r.activity_number),
                    "a_type": r.activity_type,
                    "a_inst": r.activity_instruction or "",
                    "f_id": str(r.fragment_id),
                    "f_text": r.normalized_text,
                    "f_pdf": r.pdf_page,
                    "f_printed": r.printed_page,
                    "embedding": emb,
                }
                session.run(cypher, params).consume()

            print(f"  Processed {min(i + batch_size, total_rows)}/{total_rows} fragments...")

    print("  ✓ All structural fragments successfully embedded and indexed.")

    # 5. Populate Pedagogical Knowledge Concepts & Weighted Relationships
    print("\n[5/5] Building Pedagogical Semantic Layer & Weighted Relationships...")
    ontology = get_curriculum_ontology()

    # 5.1 Topics
    print(f"  • Upserting {len(ontology.topics)} Topics...")
    topic_texts = [f"Topic {t.name}: {t.description}" for t in ontology.topics]
    topic_embeddings = embedder.embed_batch(topic_texts)
    for topic, emb in zip(ontology.topics, topic_embeddings):
        repo.upsert_topic(topic, emb)

    # 5.2 Grammar Rules
    print(f"  • Upserting {len(ontology.grammar_rules)} Grammar Rules...")
    grammar_texts = [
        f"Grammar {g.name}. Formula: {g.formula}. {g.explanation_vi}. Examples: {' '.join(g.examples)}"
        for g in ontology.grammar_rules
    ]
    grammar_embeddings = embedder.embed_batch(grammar_texts)
    for rule, emb in zip(ontology.grammar_rules, grammar_embeddings):
        repo.upsert_grammar_rule(rule, emb)

    # 5.3 Vocabulary
    print(f"  • Upserting {len(ontology.vocabulary)} Vocabulary items...")
    vocab_texts = [
        f"Word {v.word} ({v.pos}, {v.ipa}): {v.meaning_vi}. Example: {v.example}"
        for v in ontology.vocabulary
    ]
    vocab_embeddings = embedder.embed_batch(vocab_texts)
    for vocab, emb in zip(ontology.vocabulary, vocab_embeddings):
        repo.upsert_vocabulary(vocab, emb)

    # 5.4 Pronunciation Sounds
    print(f"  • Upserting {len(ontology.pronunciations)} Pronunciation Sounds...")
    pron_texts = [
        f"Pronunciation sound {p.symbol}: {p.description}. Sample words: {', '.join(p.sample_words)}"
        for p in ontology.pronunciations
    ]
    pron_embeddings = embedder.embed_batch(pron_texts)
    for pron, emb in zip(ontology.pronunciations, pron_embeddings):
        repo.upsert_pronunciation(pron, emb)

    # 5.5 Link Review Units via REVIEWS (weight: 0.8)
    review_links = [
        (31, [1, 2, 3]),
        (61, [4, 5, 6]),
        (91, [7, 8, 9]),
        (121, [10, 11, 12]),
    ]
    with neo4j_driver.session() as session:
        for rev_num, target_nums in review_links:
            for tgt_num in target_nums:
                session.run("""
                    MATCH (rev:Unit {number: $rev_num})
                    MATCH (tgt:Unit {number: $tgt_num})
                    MERGE (rev)-[r:REVIEWS]->(tgt)
                    SET r.weight = 0.8
                """, {"rev_num": rev_num, "tgt_num": tgt_num}).consume()
    print("  ✓ Review units linked via REVIEWS relationships (weight: 0.8).")

    # 5.6 Link Grammar Rules via PREREQUISITE_OF (weight: 0.7)
    with neo4j_driver.session() as session:
        for prereq in ontology.prerequisites:
            session.run("""
                MATCH (p:GrammarRule {id: $prereq_id})
                MATCH (t:GrammarRule {id: $target_id})
                MERGE (p)-[r:PREREQUISITE_OF]->(t)
                SET r.weight = $weight
            """, {
                "prereq_id": prereq.prerequisite_id,
                "target_id": prereq.target_id,
                "weight": prereq.weight,
            }).consume()
    print("  ✓ Grammar rules linked via PREREQUISITE_OF relationships (weight: 0.7).")

    # 5.7 Link Activities & Fragments to Pedagogical Nodes with Weights
    print("  • Linking Activities and Fragments to Pedagogical Entities with weights...")
    with neo4j_driver.session() as session:
        # Link to Topics via APPEARS_IN (weight: 0.5)
        session.run("""
            MATCH (u:Unit)
            MATCH (t:Topic {unit_number: u.number})
            MATCH (u)-[:HAS_SECTION]->(s:Section)-[:HAS_ACTIVITY]->(a:Activity)-[:HAS_SOURCE]->(f:SourceFragment)
            MERGE (f)-[r:APPEARS_IN]->(t)
            SET r.weight = 0.5
        """).consume()

        # Link A CLOSER LOOK 2 activities to GrammarRule via TEACHES (1.0) and PRACTICES (0.6)
        session.run("""
            MATCH (u:Unit)-[:HAS_SECTION]->(s:Section)
            WHERE s.title CONTAINS 'A CLOSER LOOK 2'
            MATCH (g:GrammarRule {unit_number: u.number})
            MATCH (s)-[:HAS_ACTIVITY]->(a:Activity)-[:HAS_SOURCE]->(f:SourceFragment)
            WHERE a.number IN ['1', '2']
            MERGE (f)-[r:TEACHES]->(g)
            SET r.weight = 1.0
        """).consume()

        session.run("""
            MATCH (u:Unit)-[:HAS_SECTION]->(s:Section)
            WHERE s.title CONTAINS 'A CLOSER LOOK 2'
            MATCH (g:GrammarRule {unit_number: u.number})
            MATCH (s)-[:HAS_ACTIVITY]->(a:Activity)-[:HAS_SOURCE]->(f:SourceFragment)
            WHERE a.number IN ['3', '4', '5']
            MERGE (f)-[r:PRACTICES]->(g)
            SET r.weight = 0.6
        """).consume()

        # Link A CLOSER LOOK 1 (Pronunciation) to PronunciationSound via TEACHES (1.0)
        session.run("""
            MATCH (u:Unit)-[:HAS_SECTION]->(s:Section)
            WHERE s.title CONTAINS 'A CLOSER LOOK 1'
            MATCH (p:PronunciationSound {unit_number: u.number})
            MATCH (s)-[:HAS_ACTIVITY]->(a:Activity)-[:HAS_SOURCE]->(f:SourceFragment)
            WHERE a.activity_type = 'pronunciation' OR a.instruction CONTAINS 'listen and repeat'
            MERGE (f)-[r:TEACHES]->(p)
            SET r.weight = 1.0
        """).consume()

        # Link Vocabulary to Unit fragments via EXPLAINS (0.9) and PRACTICES (0.6)
        session.run("""
            MATCH (v:Vocabulary)
            MATCH (u:Unit {number: v.unit_number})-[:HAS_SECTION]->(s:Section)-[:HAS_ACTIVITY]->(a:Activity)-[:HAS_SOURCE]->(f:SourceFragment)
            WHERE toLower(f.text) CONTAINS toLower(v.word)
            MERGE (f)-[r:EXPLAINS]->(v)
            SET r.weight = 0.9
        """).consume()

    print("  ✓ All pedagogical relationships and weights established.")

    # 6. Verification Summary
    print("\n" + "=" * 70)
    print("📊 VERIFYING KNOWLEDGE GRAPH INTEGRITY & METRICS")
    print("=" * 70)
    with neo4j_driver.session() as session:
        nodes = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC").data()
        print("\nNode Counts by Label:")
        for row in nodes:
            print(f"  • {row['label']:<24}: {row['count']}")

        rels = session.run("MATCH ()-[r]->() RETURN type(r) as rel, count(r) as count, round(avg(coalesce(r.weight, 1.0)), 2) as avg_weight ORDER BY count DESC").data()
        print("\nRelationship Counts & Average Weights:")
        for row in rels:
            print(f"  • {row['rel']:<24}: count={row['count']:<5} (avg_weight={row['avg_weight']})")

        vec_check = session.run("MATCH (f:SourceFragment) WHERE f.embedding IS NOT NULL RETURN size(f.embedding) as dims LIMIT 1").single()
        print(f"\nVector Dimensions check: {vec_check['dims']} (expected 384)")

    neo4j_driver.close()
    elapsed = time.time() - start_time
    print(f"\n🎉 KNOWLEDGE GRAPH BUILD COMPLETE IN {elapsed:.2f}s!")
    print("=" * 70)


if __name__ == "__main__":
    main()
