from uuid import UUID
from sqlalchemy import JSON, ForeignKey, String, UnicodeText, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from english7.db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class SpeakingAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = 'speaking_attempts'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), index=True)
    # Snapshot survives deleting a personal card; no relationship/cascade.
    card_id: Mapped[UUID] = mapped_column(Uuid)
    request_hash: Mapped[str] = mapped_column(String(64))
    voice_id: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(UnicodeText)
    transcript: Mapped[str] = mapped_column(UnicodeText)
    source_label: Mapped[str] = mapped_column(UnicodeText)
    result: Mapped[dict] = mapped_column(JSON)


class SpeakingPreference(Base):
    __tablename__ = 'speaking_preferences'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), primary_key=True)
    voice_id: Mapped[str] = mapped_column(String(100))
