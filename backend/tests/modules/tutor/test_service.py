from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.modules.ai.contracts import AIResponse, Language
from english7.modules.retrieval.service import (
    Citation,
    GroundedContext,
    RetrievalCandidate,
)
from english7.modules.tutor.service import TutorService


def grounded_context() -> GroundedContext:
    fragment = RetrievalCandidate(
        fragment_id=uuid4(),
        unit_number=2,
        text="Exercise every day to stay healthy.",
        pdf_page=22,
        printed_page=20,
        vector_score=0.94,
        has_verified_source=True,
        hierarchy=("English 7", "Unit 2", "A Closer Look", "Activity 2"),
    )
    return GroundedContext(
        (fragment,),
        (Citation(fragment.fragment_id, fragment.pdf_page, fragment.printed_page),),
    )


class FakeRetrieval:
    def __init__(self, context: GroundedContext) -> None:
        self.context = context
        self.queries = []

    def retrieve(self, query: str) -> GroundedContext:
        self.queries.append(query)
        return self.context


class FakeProvider:
    def __init__(self, responder) -> None:
        self.responder = responder
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.responder(request)


def test_tutor_does_not_call_llm_without_grounded_context() -> None:
    provider = FakeProvider(lambda _: pytest.fail("provider must not be called"))
    service = TutorService(FakeRetrieval(GroundedContext((), ())), provider)

    with pytest.raises(ApplicationError) as captured:
        service.ask("Tell me about algebra", Language.ENGLISH)

    assert captured.value.code == "out_of_scope"
    assert provider.requests == []


def test_tutor_rejects_citation_not_present_in_context() -> None:
    context = grounded_context()
    provider = FakeProvider(
        lambda request: AIResponse(
            "Unsupported", request.language, (uuid4(),)
        )
    )
    service = TutorService(FakeRetrieval(context), provider)

    with pytest.raises(ApplicationError) as captured:
        service.ask("How can I stay healthy?", Language.ENGLISH)

    assert captured.value.code == "invalid_ai_citations"


def test_language_mode_changes_presentation_but_not_evidence() -> None:
    context = grounded_context()

    def respond(request):
        answer = "Tập thể dục mỗi ngày." if request.language == "vi" else "Exercise daily."
        return AIResponse(answer, request.language, (request.evidence[0].fragment_id,))

    provider = FakeProvider(respond)
    service = TutorService(FakeRetrieval(context), provider)

    vietnamese = service.ask("How can I stay healthy?", Language.VIETNAMESE)
    english = service.ask("How can I stay healthy?", Language.ENGLISH)

    assert vietnamese.answer != english.answer
    assert provider.requests[0].evidence == provider.requests[1].evidence
    assert vietnamese.citations == english.citations


def test_tutor_rejects_language_mismatch() -> None:
    context = grounded_context()
    provider = FakeProvider(
        lambda request: AIResponse(
            "Wrong language", Language.ENGLISH, (request.evidence[0].fragment_id,)
        )
    )
    service = TutorService(FakeRetrieval(context), provider)

    with pytest.raises(ApplicationError) as captured:
        service.ask("Giữ sức khỏe thế nào?", Language.VIETNAMESE)

    assert captured.value.code == "invalid_ai_response"
