import os
import math
import time
from uuid import uuid4

import pytest
from neo4j import GraphDatabase

from english7.modules.knowledge.contracts import IndexedFragment
from english7.modules.knowledge.neo4j_repository import Neo4jKnowledgeRepository


@pytest.mark.integration
def test_neo4j_upsert_and_vector_query() -> None:
    uri = os.getenv("NEO4J_TEST_URI")
    user = os.getenv("NEO4J_TEST_USER")
    password = os.getenv("NEO4J_TEST_PASSWORD")
    if not all((uri, user, password)):
        pytest.skip("Neo4j integration environment is not configured")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    repository = Neo4jKnowledgeRepository(
        driver,
        vector_index_name="fragment_embedding_test",
        embedding_dimensions=2,
        graph_result_limit=10,
    )
    fragment_id = uuid4()
    angle = (fragment_id.int % 10_000) / 10_000 * math.tau
    embedding = [math.cos(angle), math.sin(angle)]
    fragment = IndexedFragment(
        fragment_id=fragment_id,
        textbook_id=uuid4(),
        unit_id=uuid4(),
        section_id=uuid4(),
        activity_id=uuid4(),
        unit_number=1,
        text="collecting dolls is a hobby",
        pdf_page=12,
        printed_page=10,
        embedding=embedding,
        hierarchy=("English 7", "Unit 1: Hobbies", "Getting Started", "1"),
    )
    try:
        repository.ensure_schema()
        repository.upsert_fragment(fragment)
        results = []
        for _ in range(20):
            try:
                results = repository.vector_search(embedding, 5)
            except Exception as error:
                if "POPULATING" not in str(error):
                    raise
            if results:
                break
            time.sleep(0.25)
    finally:
        driver.close()

    assert results[0].fragment_id == fragment_id
    assert results[0].has_verified_source is True
