import re
from uuid import UUID

from neo4j import Driver

from english7.modules.knowledge.contracts import IndexedFragment
from english7.modules.knowledge.curriculum_ontology import (
    PedagogicalGrammarRule,
    PedagogicalPronunciation,
    PedagogicalTopic,
    PedagogicalVocabulary,
)
from english7.modules.retrieval.service import RetrievalCandidate

_CYPHER_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class Neo4jKnowledgeRepository:
    def __init__(
        self,
        driver: Driver,
        *,
        vector_index_name: str,
        embedding_dimensions: int,
        graph_result_limit: int,
        database: str | None = None,
    ) -> None:
        if not _CYPHER_IDENTIFIER.fullmatch(vector_index_name):
            raise ValueError("Vector index name is not a safe Cypher identifier")
        if embedding_dimensions <= 0 or graph_result_limit <= 0:
            raise ValueError("Neo4j retrieval limits must be positive")
        self._driver = driver
        self._index_name = vector_index_name
        self._dimensions = embedding_dimensions
        self._graph_result_limit = graph_result_limit
        self._database = database

    def ensure_schema(self) -> None:
        constraints = [
            "CREATE CONSTRAINT source_fragment_sql_id IF NOT EXISTS FOR (fragment:SourceFragment) REQUIRE fragment.sql_id IS UNIQUE",
            "CREATE CONSTRAINT knowledge_concept_id IF NOT EXISTS FOR (concept:KnowledgeConcept) REQUIRE concept.id IS UNIQUE",
        ]
        indexes = [
            (
                f"CREATE VECTOR INDEX {self._index_name} IF NOT EXISTS "
                "FOR (fragment:SourceFragment) ON (fragment.embedding) "
                "OPTIONS {indexConfig: {"
                f"`vector.dimensions`: {self._dimensions}, "
                "`vector.similarity_function`: 'cosine'}}"
            ),
            (
                "CREATE VECTOR INDEX knowledge_concept_embedding IF NOT EXISTS "
                "FOR (concept:KnowledgeConcept) ON (concept.embedding) "
                "OPTIONS {indexConfig: {"
                f"`vector.dimensions`: {self._dimensions}, "
                "`vector.similarity_function`: 'cosine'}}"
            ),
        ]
        with self._driver.session(database=self._database) as session:
            for constraint in constraints:
                session.run(constraint).consume()
            for vector_index in indexes:
                session.run(vector_index).consume()

    def upsert_fragment(self, fragment: IndexedFragment) -> None:
        if len(fragment.embedding) != self._dimensions:
            raise ValueError("Embedding dimensions do not match the vector index")
        query = """
        MERGE (textbook:Textbook {sql_id: $textbook_id})
        SET textbook.title = $textbook_title
        MERGE (unit:Unit {sql_id: $unit_id})
        SET unit.number = $unit_number, unit.title = $unit_title
        MERGE (section:Section {sql_id: $section_id})
        SET section.title = $section_title
        MERGE (activity:Activity {sql_id: $activity_id})
        MERGE (fragment:SourceFragment {sql_id: $fragment_id})
        SET fragment.text = $text,
            fragment.pdf_page = $pdf_page,
            fragment.printed_page = $printed_page,
            fragment.unit_number = $unit_number,
            fragment.embedding = $embedding,
            fragment.verified = true,
            fragment.hierarchy = $hierarchy
        MERGE (textbook)-[:HAS_UNIT]->(unit)
        MERGE (unit)-[:HAS_SECTION]->(section)
        MERGE (section)-[:HAS_ACTIVITY]->(activity)
        MERGE (activity)-[:HAS_SOURCE]->(fragment)
        """
        parameters = {
            "textbook_id": str(fragment.textbook_id),
            "textbook_title": fragment.hierarchy[0],
            "unit_id": str(fragment.unit_id),
            "unit_number": fragment.unit_number,
            "unit_title": fragment.hierarchy[1],
            "section_id": str(fragment.section_id),
            "section_title": fragment.hierarchy[2],
            "activity_id": str(fragment.activity_id),
            "fragment_id": str(fragment.fragment_id),
            "text": fragment.text,
            "pdf_page": fragment.pdf_page,
            "printed_page": fragment.printed_page,
            "embedding": fragment.embedding,
            "hierarchy": list(fragment.hierarchy),
        }
        with self._driver.session(database=self._database) as session:
            session.run(query, parameters).consume()

    @staticmethod
    def _candidate(record) -> RetrievalCandidate:
        node = record["fragment"]
        return RetrievalCandidate(
            fragment_id=UUID(node["sql_id"]),
            unit_number=node["unit_number"],
            text=node["text"],
            pdf_page=node["pdf_page"],
            printed_page=node.get("printed_page"),
            vector_score=float(record.get("score", 0.0)),
            has_verified_source=bool(node.get("verified", False)),
            hierarchy=tuple(node["hierarchy"]),
        )

    def vector_search(
        self, query_vector: list[float], top_k: int
    ) -> list[RetrievalCandidate]:
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $query_vector)
        YIELD node AS fragment, score
        WHERE fragment.verified = true
        RETURN fragment, score
        ORDER BY score DESC, fragment.sql_id
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(
                query,
                index_name=self._index_name,
                top_k=top_k,
                query_vector=query_vector,
            )
            return [self._candidate(record) for record in records]

    def expand(
        self, fragment_ids: tuple[UUID, ...], max_depth: int
    ) -> list[RetrievalCandidate]:
        if max_depth <= 0:
            raise ValueError("Graph depth must be positive")
        depth = min(max_depth, 8)
        query = f"""
        MATCH (seed:SourceFragment)
        WHERE seed.sql_id IN $fragment_ids
        MATCH path = (seed)-[*1..{depth}]-(neighbor:SourceFragment)
        WHERE neighbor.verified = true AND NOT neighbor.sql_id IN $fragment_ids
        WITH neighbor, min(length(path)) AS distance
        RETURN neighbor AS fragment, 0.0 AS score
        ORDER BY distance, fragment.sql_id
        LIMIT $result_limit
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(
                query,
                fragment_ids=[str(fragment_id) for fragment_id in fragment_ids],
                result_limit=self._graph_result_limit,
            )
            return [self._candidate(record) for record in records]

    def upsert_topic(self, topic: PedagogicalTopic, embedding: list[float]) -> None:
        query = """
        MERGE (t:Topic:KnowledgeConcept {id: $id})
        SET t.unit_number = $unit_number,
            t.name = $name,
            t.description = $description,
            t.embedding = $embedding
        """
        params = {
            "id": topic.id,
            "unit_number": topic.unit_number,
            "name": topic.name,
            "description": topic.description,
            "embedding": embedding,
        }
        with self._driver.session(database=self._database) as session:
            session.run(query, params).consume()

    def upsert_grammar_rule(self, rule: PedagogicalGrammarRule, embedding: list[float]) -> None:
        query = """
        MERGE (g:GrammarRule:KnowledgeConcept {id: $id})
        SET g.unit_number = $unit_number,
            g.name = $name,
            g.formula = $formula,
            g.explanation_vi = $explanation_vi,
            g.examples = $examples,
            g.embedding = $embedding
        """
        params = {
            "id": rule.id,
            "unit_number": rule.unit_number,
            "name": rule.name,
            "formula": rule.formula,
            "explanation_vi": rule.explanation_vi,
            "examples": rule.examples,
            "embedding": embedding,
        }
        with self._driver.session(database=self._database) as session:
            session.run(query, params).consume()

    def upsert_vocabulary(self, vocab: PedagogicalVocabulary, embedding: list[float]) -> None:
        query = """
        MERGE (v:Vocabulary:KnowledgeConcept {id: $id})
        SET v.unit_number = $unit_number,
            v.word = $word,
            v.pos = $pos,
            v.ipa = $ipa,
            v.meaning_vi = $meaning_vi,
            v.example = $example,
            v.embedding = $embedding
        """
        params = {
            "id": vocab.id,
            "unit_number": vocab.unit_number,
            "word": vocab.word,
            "pos": vocab.pos,
            "ipa": vocab.ipa,
            "meaning_vi": vocab.meaning_vi,
            "example": vocab.example,
            "embedding": embedding,
        }
        with self._driver.session(database=self._database) as session:
            session.run(query, params).consume()

    def upsert_pronunciation(self, pron: PedagogicalPronunciation, embedding: list[float]) -> None:
        query = """
        MERGE (p:PronunciationSound:KnowledgeConcept {id: $id})
        SET p.unit_number = $unit_number,
            p.symbol = $symbol,
            p.description = $description,
            p.sample_words = $sample_words,
            p.embedding = $embedding
        """
        params = {
            "id": pron.id,
            "unit_number": pron.unit_number,
            "symbol": pron.symbol,
            "description": pron.description,
            "sample_words": pron.sample_words,
            "embedding": embedding,
        }
        with self._driver.session(database=self._database) as session:
            session.run(query, params).consume()

    def upsert_weighted_relationship(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        rel_type: str,
        weight: float,
    ) -> None:
        src_id_prop = "sql_id" if source_label in ("SourceFragment", "Activity", "Section", "Unit", "Textbook") else "id"
        tgt_id_prop = "sql_id" if target_label in ("SourceFragment", "Activity", "Section", "Unit", "Textbook") else "id"
        query = f"""
        MATCH (s:{source_label} {{{src_id_prop}: $source_id}})
        MATCH (t:{target_label} {{{tgt_id_prop}: $target_id}})
        MERGE (s)-[r:{rel_type}]->(t)
        SET r.weight = $weight
        """
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "weight": weight,
        }
        with self._driver.session(database=self._database) as session:
            session.run(query, params).consume()

    def weighted_graph_search(
        self, seed_fragment_ids: tuple[UUID, ...], max_depth: int = 2
    ) -> list[tuple[RetrievalCandidate, float]]:
        depth = min(max(max_depth, 1), 4)
        query = f"""
        MATCH (seed:SourceFragment)
        WHERE seed.sql_id IN $fragment_ids
        MATCH path = (seed)-[r:TEACHES|EXPLAINS|PRACTICES|APPEARS_IN|PREREQUISITE_OF*1..{depth}]-(neighbor:SourceFragment)
        WHERE neighbor.verified = true AND NOT neighbor.sql_id IN $fragment_ids
        WITH neighbor,
             reduce(w = 1.0, rel IN relationships(path) | w * coalesce(rel.weight, 0.5)) AS path_weight,
             length(path) AS dist
        WITH neighbor, max(path_weight * (0.8 ^ (dist - 1))) AS score
        RETURN neighbor AS fragment, score
        ORDER BY score DESC, fragment.sql_id
        LIMIT $result_limit
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(
                query,
                fragment_ids=[str(fid) for fid in seed_fragment_ids],
                result_limit=self._graph_result_limit,
            )
            return [
                (self._candidate(record), float(record.get("score", 0.5)))
                for record in records
            ]

