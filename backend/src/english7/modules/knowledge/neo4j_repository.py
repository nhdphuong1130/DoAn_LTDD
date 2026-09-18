import re
from uuid import UUID

from neo4j import Driver

from english7.modules.knowledge.contracts import IndexedFragment
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
        constraint = (
            "CREATE CONSTRAINT source_fragment_sql_id IF NOT EXISTS "
            "FOR (fragment:SourceFragment) REQUIRE fragment.sql_id IS UNIQUE"
        )
        vector_index = (
            f"CREATE VECTOR INDEX {self._index_name} IF NOT EXISTS "
            "FOR (fragment:SourceFragment) ON (fragment.embedding) "
            "OPTIONS {indexConfig: {"
            f"`vector.dimensions`: {self._dimensions}, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        with self._driver.session(database=self._database) as session:
            session.run(constraint).consume()
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
