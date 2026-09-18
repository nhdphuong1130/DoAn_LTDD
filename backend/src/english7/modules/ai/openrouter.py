import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.request import Request, urlopen
from uuid import UUID

from pydantic import SecretStr

from english7.modules.ai.contracts import AIRequest, AIResponse, Language


@dataclass(slots=True)
class AIProviderError(Exception):
    code: str
    message: str = "The AI provider request failed"

    def __str__(self) -> str:
        return self.message


class JSONHTTPClient(Protocol):
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]: ...


class UrllibJSONClient:
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


class OpenRouterProvider:
    def __init__(
        self,
        *,
        http: JSONHTTPClient,
        api_key: SecretStr,
        endpoint: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        if not endpoint.startswith("https://"):
            raise ValueError("OpenRouter endpoint must use HTTPS")
        if not model.strip() or timeout_seconds <= 0:
            raise ValueError("OpenRouter model and positive timeout are required")
        self._http = http
        self._api_key = api_key
        self._endpoint = endpoint
        self._model = model
        self._timeout = timeout_seconds

    @staticmethod
    def _messages(request: AIRequest) -> list[dict[str, str]]:
        evidence = [
            {
                "fragment_id": str(item.fragment_id),
                "text": item.text,
                "pdf_page": item.pdf_page,
                "printed_page": item.printed_page,
            }
            for item in request.evidence
        ]
        system = (
            "You are a closed-world English 7 tutor. Use only the supplied "
            "verified textbook evidence. Return JSON with answer, language, and "
            "citations. citations must contain only supplied fragment_id values. "
            "Do not add outside facts."
        )
        user = json.dumps(
            {
                "question": request.question,
                "language": request.language.value,
                "evidence": evidence,
            },
            ensure_ascii=False,
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def generate(self, request: AIRequest) -> AIResponse:
        payload = {
            "model": self._model,
            "messages": self._messages(request),
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        try:
            response = self._http.post_json(
                self._endpoint,
                headers=headers,
                payload=payload,
                timeout_seconds=self._timeout,
            )
            content = response["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return AIResponse(
                answer=str(parsed["answer"]).strip(),
                language=Language(parsed["language"]),
                citations=tuple(UUID(value) for value in parsed["citations"]),
            )
        except Exception as error:
            if isinstance(error, AIProviderError):
                raise
            raise AIProviderError("ai_provider_failed") from None


class OpenRouterEmbedder:
    def __init__(
        self,
        *,
        http: JSONHTTPClient,
        api_key: SecretStr,
        endpoint: str,
        model: str,
        dimensions: int,
        timeout_seconds: float,
    ) -> None:
        if not endpoint.startswith("https://"):
            raise ValueError("OpenRouter endpoint must use HTTPS")
        if not model.strip() or dimensions <= 0 or timeout_seconds <= 0:
            raise ValueError("Embedding model, dimensions, and timeout are required")
        self._http = http
        self._api_key = api_key
        self._endpoint = endpoint
        self._model = model
        self._dimensions = dimensions
        self._timeout = timeout_seconds

    def embed(self, text: str) -> list[float]:
        try:
            response = self._http.post_json(
                self._endpoint,
                headers={
                    "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                payload={
                    "model": self._model,
                    "input": text,
                    "dimensions": self._dimensions,
                },
                timeout_seconds=self._timeout,
            )
            vector = [float(value) for value in response["data"][0]["embedding"]]
            if len(vector) != self._dimensions:
                raise ValueError("Unexpected embedding dimensions")
            return vector
        except Exception:
            raise AIProviderError(
                "embedding_provider_failed", "Embedding provider request failed"
            ) from None
