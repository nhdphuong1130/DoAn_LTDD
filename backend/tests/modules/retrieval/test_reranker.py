from english7.modules.retrieval.reranker import reciprocal_rank_fusion


def test_rrf_fuses_rankings_deterministically_without_mixing_raw_scores() -> None:
    fused = reciprocal_rank_fusion(
        vector_ids=("a", "b", "c"),
        graph_ids=("b", "d", "a"),
        rank_constant=60,
    )

    assert [item.item_id for item in fused] == ["b", "a", "d", "c"]
    assert fused[0].score > fused[1].score > fused[2].score
