from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from english7.modules.knowledge import fastembed_service


@pytest.fixture
def boundary(monkeypatch):
    created, inputs = [], []

    class FakeEmbedding:
        def __init__(self, **kwargs):
            created.append(kwargs)

        def embed(self, texts):
            inputs.append(list(texts))
            return [[1, 2.5] for _ in texts]

    monkeypatch.setattr(fastembed_service, 'TextEmbedding', FakeEmbedding)
    return created, inputs


def test_constructor_and_empty_batch_do_not_load_model(boundary):
    created, inputs = boundary
    service = fastembed_service.FastEmbedService()
    assert created == []
    assert service.embed_batch([]) == []
    assert created == inputs == []


def test_first_use_preserves_model_and_persistent_cache_configuration(boundary, tmp_path):
    created, inputs = boundary
    service = fastembed_service.FastEmbedService(
        model_name='configured/model', cache_dir=str(tmp_path),
    )
    assert created == []
    assert service.embed(' Hello world ') == [1.0, 2.5]
    assert service.embed_batch([' one ', '', '   ']) == [[1.0, 2.5]] * 3
    assert created == [{'model_name': 'configured/model', 'cache_dir': str(tmp_path)}]
    assert inputs == [['Hello world'], ['one', 'empty', 'empty']]


def test_load_failure_is_deferred_and_can_retry(monkeypatch):
    attempts = []

    class RetryingEmbedding:
        def __init__(self, **kwargs):
            attempts.append(kwargs)
            if len(attempts) == 1:
                raise RuntimeError('model download unavailable')

        def embed(self, texts):
            return [[0.5] for _ in texts]

    monkeypatch.setattr(fastembed_service, 'TextEmbedding', RetryingEmbedding)
    service = fastembed_service.FastEmbedService()
    assert attempts == []
    with pytest.raises(RuntimeError, match='download unavailable'):
        service.embed('test')
    assert service.embed('test') == [0.5]
    assert len(attempts) == 2


def test_simultaneous_first_queries_share_one_model(boundary):
    created, _ = boundary
    service = fastembed_service.FastEmbedService()
    assert created == []
    barrier = Barrier(4)

    def query(_):
        barrier.wait(timeout=5)
        return service.embed('test')

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(query, range(4))) == [[1.0, 2.5]] * 4
    assert len(created) == 1
