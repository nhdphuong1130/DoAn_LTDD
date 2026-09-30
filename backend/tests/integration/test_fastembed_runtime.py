"""Real-model smoke checks; explicitly opt in with ENGLISH7_TEST_FASTEMBED=1."""
import math
import os

import pytest

from english7.modules.knowledge.fastembed_service import FastEmbedService

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv('ENGLISH7_TEST_FASTEMBED') != '1',
        reason='Opt in to real FastEmbed model inference and potential downloads',
    ),
]


@pytest.fixture(scope='module')
def service():
    return FastEmbedService(cache_dir=os.getenv('ENGLISH7_EMBEDDING_CACHE_DIR'))


def test_real_model_dimensions_and_batch(service):
    vector = service.embed('Hello world, this is English 7 textbook.')
    assert len(vector) == 384
    assert all(isinstance(value, float) for value in vector)
    vectors = service.embed_batch(['Present simple tense', 'Renewable energy sources'])
    assert len(vectors) == 2
    assert all(len(vector) == 384 for vector in vectors)


def test_real_model_semantic_similarity(service):
    road = service.embed('traffic lights and road signs')
    related = service.embed('traffic rules and vehicles on the road')
    unrelated = service.embed('cooking delicious food and noodles')

    def cosine(a, b):
        return sum(x * y for x, y in zip(a, b)) / (
            math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
        )

    assert cosine(road, related) > cosine(road, unrelated)
