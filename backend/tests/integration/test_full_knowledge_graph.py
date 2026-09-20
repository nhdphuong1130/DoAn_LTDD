import pytest
from neo4j import GraphDatabase
from english7.core.settings import get_settings


@pytest.mark.integration
def test_full_knowledge_graph_populated_and_indexed():
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
    )
    with driver.session() as session:
        # Check SourceFragments count
        frag_count = session.run("MATCH (f:SourceFragment) RETURN count(f) as count").single()["count"]
        assert frag_count >= 400

        # Check Pedagogical Nodes
        concept_count = session.run("MATCH (c:KnowledgeConcept) RETURN count(c) as count").single()["count"]
        assert concept_count >= 40

        # Check Weighted Relationships
        teaches_count = session.run("MATCH ()-[r:TEACHES]->() RETURN count(r) as count").single()["count"]
        assert teaches_count > 0

        # Check Vectors have 384 dimensions
        sample = session.run("MATCH (f:SourceFragment) WHERE f.embedding IS NOT NULL RETURN size(f.embedding) as dims LIMIT 1").single()
        assert sample is not None
        assert sample["dims"] == 384
    driver.close()
