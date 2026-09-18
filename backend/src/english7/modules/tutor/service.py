from dataclasses import dataclass

from english7.api.errors import ApplicationError
from english7.modules.ai.contracts import AIProvider, AIRequest, Evidence, Language
from english7.modules.retrieval.service import Citation, RetrievalRepository


@dataclass(frozen=True, slots=True)
class TutorAnswer:
    answer: str
    language: Language
    citations: tuple[Citation, ...]


class ContextRetriever(RetrievalRepository):
    def retrieve(self, query: str): ...


class TutorService:
    def __init__(self, retrieval, provider: AIProvider) -> None:
        self._retrieval = retrieval
        self._provider = provider

    def ask(self, question: str, language: Language) -> TutorAnswer:
        context = self._retrieval.retrieve(question)
        if not context.fragments:
            raise ApplicationError(
                "out_of_scope",
                "No verified textbook evidence was found for this question",
                422,
            )
        evidence = tuple(
            Evidence(
                item.fragment_id,
                item.text,
                item.pdf_page,
                item.printed_page,
            )
            for item in context.fragments
        )
        generated = self._provider.generate(AIRequest(question, language, evidence))
        if generated.language != language or not generated.answer:
            raise ApplicationError(
                "invalid_ai_response", "AI response validation failed", 502
            )
        allowed = {item.fragment_id for item in evidence}
        if not generated.citations or not set(generated.citations).issubset(allowed):
            raise ApplicationError(
                "invalid_ai_citations", "AI citations failed source validation", 502
            )
        citations_by_id = {
            citation.fragment_id: citation for citation in context.citations
        }
        try:
            citations = tuple(
                citations_by_id[fragment_id] for fragment_id in generated.citations
            )
        except KeyError:
            raise ApplicationError(
                "invalid_ai_citations", "AI citations failed source validation", 502
            ) from None
        return TutorAnswer(generated.answer, generated.language, citations)
