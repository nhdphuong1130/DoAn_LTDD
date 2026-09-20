import pytest
from unittest.mock import MagicMock
from english7.modules.knowledge.neo4j_repository import Neo4jKnowledgeRepository
from english7.modules.knowledge.curriculum_ontology import (
    PedagogicalTopic,
    PedagogicalGrammarRule,
    PedagogicalVocabulary,
    PedagogicalPronunciation,
)


def test_neo4j_repository_ensures_dual_vector_indexes():
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    repo = Neo4jKnowledgeRepository(
        mock_driver,
        vector_index_name="source_fragment_embedding",
        embedding_dimensions=384,
        graph_result_limit=10,
    )
    repo.ensure_schema()
    calls = [call[0][0] for call in mock_session.run.call_args_list]
    assert any("source_fragment_embedding" in c for c in calls)
    assert any("knowledge_concept_embedding" in c for c in calls)


def test_neo4j_repository_upsert_pedagogical_nodes():
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    repo = Neo4jKnowledgeRepository(
        mock_driver,
        vector_index_name="source_fragment_embedding",
        embedding_dimensions=384,
        graph_result_limit=10,
    )
    topic = PedagogicalTopic("topic-u1", 1, "Hobbies", "Sở thích")
    repo.upsert_topic(topic, [0.1] * 384)
    assert mock_session.run.called

    rule = PedagogicalGrammarRule("rule-u1", 1, "Present Simple", "S+V", "Thì HTĐ", ["I read."])
    repo.upsert_grammar_rule(rule, [0.1] * 384)
    assert mock_session.run.called

    vocab = PedagogicalVocabulary("v-1", 1, "hobby", "noun", "/h/", "sở thích", "my hobby")
    repo.upsert_vocabulary(vocab, [0.1] * 384)
    assert mock_session.run.called

    pron = PedagogicalPronunciation("p-1", 1, "/ə/", "schwa", ["yoga"])
    repo.upsert_pronunciation(pron, [0.1] * 384)
    assert mock_session.run.called


def test_neo4j_repository_upsert_weighted_relationship():
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    repo = Neo4jKnowledgeRepository(
        mock_driver,
        vector_index_name="source_fragment_embedding",
        embedding_dimensions=384,
        graph_result_limit=10,
    )
    repo.upsert_weighted_relationship(
        source_id="frag-1",
        source_label="SourceFragment",
        target_id="rule-u1",
        target_label="GrammarRule",
        rel_type="TEACHES",
        weight=1.0,
    )
    assert mock_session.run.called
