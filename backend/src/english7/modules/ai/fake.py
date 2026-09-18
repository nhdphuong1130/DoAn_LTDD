from collections.abc import Callable

from english7.modules.ai.contracts import AIRequest, AIResponse


class FakeAIProvider:
    def __init__(self, responder: Callable[[AIRequest], AIResponse]) -> None:
        self._responder = responder
        self.requests: list[AIRequest] = []

    def generate(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        return self._responder(request)
