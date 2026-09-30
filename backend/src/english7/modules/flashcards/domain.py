from datetime import datetime
import unicodedata
from uuid import UUID

from pydantic import BaseModel


def normalize_word(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


class Deck(BaseModel):
    id: UUID
    name: str
    kind: str
    unit_number: int | None = None
    card_count: int = 0


class Card(BaseModel):
    id: UUID
    deck_id: UUID
    word: str
    meaning: str
    example: str = ''
    notes: str = ''
    image_url: str | None = None
    ipa: str | None = None
    pos: str | None = None
    source_label: str = 'Personal card'
    source_fragment_id: UUID | None = None
    unit_number: int | None = None
    page: int | None = None
    audio_url: str | None = None
    difficult: bool = False
    due_at: datetime | None = None
    review_count: int = 0


class ReviewResult(BaseModel):
    correct: bool
    meaning: str
    due_at: datetime
