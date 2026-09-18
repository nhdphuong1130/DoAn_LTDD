import logging
from uuid import uuid4

import pytest
from pydantic import SecretStr

from english7.modules.ai.contracts import (
    AIRequest,
    Evidence,
    Language,
)
from english7.modules.ai.openrouter import (
    AIProviderError,
    OpenRouterEmbedder,
    OpenRouterProvider,
)


class FakeHTTP:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.call = None

    def post_json(self, url, *, headers, payload, timeout_seconds):
        self.call = (url, headers, payload, timeout_seconds)
        if self.error:
            raise self.error
        return self.response


def request() -> AIRequest:
    fragment_id = uuid4()
    return AIRequest(
        question="What is a healthy habit?",
        language=Language.ENGLISH,
        evidence=(Evidence(fragment_id, "Exercise every day.", 20, 18),),
    )


def test_provider_uses_configured_model_timeout_and_structured_output() -> None:
    req = request()
    http = FakeHTTP(
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"answer":"Exercise every day.",'
                            '"language":"en","citations":["'
                            + str(req.evidence[0].fragment_id)
                            + '"]}'
                        )
                    }
                }
            ]
        }
    )
    provider = OpenRouterProvider(
        http=http,
        api_key=SecretStr("top-secret-key"),
        endpoint="https://openrouter.example/api/v1/chat/completions",
        model="configured/model",
        timeout_seconds=17.5,
    )

    result = provider.generate(req)

    url, headers, payload, timeout = http.call
    assert url.endswith("/chat/completions")
    assert headers["Authorization"] == "Bearer top-secret-key"
    assert payload["model"] == "configured/model"
    assert payload["response_format"] == {"type": "json_object"}
    assert timeout == 17.5
    assert result.citations == (req.evidence[0].fragment_id,)


def test_provider_never_exposes_api_key_in_errors_or_logs(caplog) -> None:
    secret = "never-log-this-key"
    provider = OpenRouterProvider(
        http=FakeHTTP(error=RuntimeError(f"request failed using {secret}")),
        api_key=SecretStr(secret),
        endpoint="https://openrouter.example/api/v1/chat/completions",
        model="configured/model",
        timeout_seconds=10,
    )

    with caplog.at_level(logging.ERROR), pytest.raises(AIProviderError) as captured:
        provider.generate(request())

    assert secret not in str(captured.value)
    assert secret not in caplog.text
    assert captured.value.code == "ai_provider_failed"


def test_embedder_uses_configured_openrouter_embedding_model() -> None:
    http = FakeHTTP({"data": [{"embedding": [0.1, 0.2, 0.3]}]})
    embedder = OpenRouterEmbedder(
        http=http,
        api_key=SecretStr("embedding-secret"),
        endpoint="https://openrouter.example/api/v1/embeddings",
        model="configured/embedding-model",
        dimensions=3,
        timeout_seconds=12,
    )

    result = embedder.embed("healthy living")

    url, headers, payload, timeout = http.call
    assert url.endswith("/embeddings")
    assert headers["Authorization"] == "Bearer embedding-secret"
    assert payload == {
        "model": "configured/embedding-model",
        "input": "healthy living",
        "dimensions": 3,
    }
    assert timeout == 12
    assert result == [0.1, 0.2, 0.3]


def test_embedder_rejects_wrong_vector_dimensions() -> None:
    embedder = OpenRouterEmbedder(
        http=FakeHTTP({"data": [{"embedding": [0.1]}]}),
        api_key=SecretStr("embedding-secret"),
        endpoint="https://openrouter.example/api/v1/embeddings",
        model="configured/embedding-model",
        dimensions=3,
        timeout_seconds=12,
    )

    with pytest.raises(AIProviderError) as captured:
        embedder.embed("healthy living")

    assert captured.value.code == "embedding_provider_failed"
