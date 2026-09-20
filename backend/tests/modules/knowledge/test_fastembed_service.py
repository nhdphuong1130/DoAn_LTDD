import math
import pytest
from english7.modules.knowledge.fastembed_service import FastEmbedService


def test_fastembed_service_generates_384_dimensions():
    service = FastEmbedService()
    vector = service.embed("Hello world, this is English 7 textbook.")
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(x, float) for x in vector)


def test_fastembed_service_batch_embedding():
    service = FastEmbedService()
    texts = ["Present simple tense", "Renewable energy sources"]
    vectors = service.embed_batch(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384


def test_fastembed_semantic_similarity():
    service = FastEmbedService()
    v1 = service.embed("traffic lights and road signs")
    v2 = service.embed("traffic rules and vehicles on the road")
    v3 = service.embed("cooking delicious food and noodles")

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb)

    sim_12 = cosine(v1, v2)
    sim_13 = cosine(v1, v3)
    assert sim_12 > sim_13
