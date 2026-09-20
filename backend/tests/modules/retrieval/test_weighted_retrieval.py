import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from english7.modules.retrieval.service import RetrievalService, RetrievalCandidate
from english7.modules.retrieval.reranker import weighted_reciprocal_rank_fusion


def test_weighted_reciprocal_rank_fusion():
    vector_ids = ("id-1", "id-2")
    graph_scored = (("id-2", 1.0), ("id-3", 0.9))
    fused = weighted_reciprocal_rank_fusion(
        vector_ids=vector_ids,
        graph_scored_ids=graph_scored,
        rank_constant=60,
        vector_multiplier=1.0,
        graph_multiplier=1.2,
    )
    assert len(fused) == 3
    # id-2 appears in both with high graph weight, should be ranked first
    assert fused[0].item_id == "id-2"


def test_weighted_graph_retrieval_service():
    mock_repo = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.embed.return_value = [0.1] * 384

    frag_practice_id = uuid4()
    frag_theory_id = uuid4()

    mock_repo.vector_search.return_value = [
        RetrievalCandidate(
            fragment_id=frag_practice_id,
            unit_number=1,
            text="Practice 1: Fill in the blank with present simple.",
            pdf_page=10,
            printed_page=9,
            vector_score=0.85,
            has_verified_source=True,
            hierarchy=("English 7", "Unit 1", "A Closer Look 2", "1"),
        )
    ]

    # Graph expansion returns theory fragment with weight 1.0
    mock_repo.weighted_graph_search.return_value = [
        (
            RetrievalCandidate(
                fragment_id=frag_theory_id,
                unit_number=1,
                text="Remember Box: We use the present simple for habits.",
                pdf_page=10,
                printed_page=9,
                vector_score=0.95,
                has_verified_source=True,
                hierarchy=("English 7", "Unit 1", "A Closer Look 2", "1"),
            ),
            1.0,
        )
    ]

    service = RetrievalService(
        repository=mock_repo,
        embedder=mock_embedder,
        allowed_units=frozenset([1, 2, 10, 11, 12]),
        top_k=5,
        min_vector_score=0.6,
        graph_depth=2,
        rrf_constant=60,
        max_context_fragments=4,
    )

    context = service.retrieve("How to use present simple?")
    assert len(context.fragments) > 0
    assert len(context.citations) > 0
    # verify weighted_graph_search was called
    assert mock_repo.weighted_graph_search.called
