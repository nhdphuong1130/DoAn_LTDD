from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class Language(StrEnum):
    VIETNAMESE = "vi"
    ENGLISH = "en"


@dataclass(frozen=True, slots=True)
class Evidence:
    fragment_id: UUID
    text: str
    pdf_page: int
    printed_page: int | None


@dataclass(frozen=True, slots=True)
class AIRequest:
    question: str
    language: Language
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True, slots=True)
class AIResponse:
    answer: str
    language: Language
    citations: tuple[UUID, ...]


class AIProvider(Protocol):
    def generate(self, request: AIRequest) -> AIResponse: ...
