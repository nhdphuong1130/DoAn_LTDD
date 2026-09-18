import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from english7.db.models import ReviewStatus


@dataclass(frozen=True, slots=True)
class TextbookEntry:
    id: UUID
    title: str


@dataclass(frozen=True, slots=True)
class SourceEntry:
    id: UUID
    filename: str
    object_key: str
    sha256: str
    page_count: int
    ingestion_version: str


@dataclass(frozen=True, slots=True)
class UnitEntry:
    id: UUID
    number: int
    title: str
    pdf_page_start: int
    pdf_page_end: int


@dataclass(frozen=True, slots=True)
class SectionEntry:
    id: UUID
    unit_number: int
    title: str
    section_type: str
    position: int


@dataclass(frozen=True, slots=True)
class ActivityEntry:
    id: UUID
    section_id: UUID
    number: str | None
    activity_type: str
    instruction: str | None


@dataclass(frozen=True, slots=True)
class FragmentEntry:
    id: UUID
    source_document_id: UUID
    activity_id: UUID | None
    unit_number: int
    pdf_page: int
    printed_page: int | None
    normalized_text: str
    review_status: ReviewStatus
    is_published: bool
    region_type: str = "text"
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0


@dataclass(frozen=True, slots=True)
class AudioEntry:
    id: UUID
    media_asset_id: UUID
    activity_id: UUID
    unit_number: int
    object_key: str
    bucket: str
    track_number: int
    mime_type: str
    size_bytes: int
    checksum: str


@dataclass(frozen=True, slots=True)
class SeedManifest:
    schema_version: int
    package_id: UUID
    textbook: TextbookEntry
    source: SourceEntry
    units: tuple[UnitEntry, ...]
    sections: tuple[SectionEntry, ...]
    activities: tuple[ActivityEntry, ...]
    fragments: tuple[FragmentEntry, ...]
    audio: tuple[AudioEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), default=str))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeedManifest":
        return cls(
            schema_version=int(data["schema_version"]),
            package_id=UUID(data["package_id"]),
            textbook=TextbookEntry(
                UUID(data["textbook"]["id"]), data["textbook"]["title"]
            ),
            source=SourceEntry(
                id=UUID(data["source"]["id"]),
                filename=data["source"]["filename"],
                object_key=data["source"]["object_key"],
                sha256=data["source"]["sha256"],
                page_count=int(data["source"]["page_count"]),
                ingestion_version=data["source"]["ingestion_version"],
            ),
            units=tuple(
                UnitEntry(
                    UUID(item["id"]),
                    int(item["number"]),
                    item["title"],
                    int(item["pdf_page_start"]),
                    int(item["pdf_page_end"]),
                )
                for item in data["units"]
            ),
            sections=tuple(
                SectionEntry(
                    UUID(item["id"]),
                    int(item["unit_number"]),
                    item["title"],
                    item["section_type"],
                    int(item["position"]),
                )
                for item in data["sections"]
            ),
            activities=tuple(
                ActivityEntry(
                    UUID(item["id"]),
                    UUID(item["section_id"]),
                    item.get("number"),
                    item["activity_type"],
                    item.get("instruction"),
                )
                for item in data["activities"]
            ),
            fragments=tuple(
                FragmentEntry(
                    id=UUID(item["id"]),
                    source_document_id=UUID(item["source_document_id"]),
                    activity_id=(
                        UUID(item["activity_id"]) if item.get("activity_id") else None
                    ),
                    unit_number=int(item["unit_number"]),
                    pdf_page=int(item["pdf_page"]),
                    printed_page=item.get("printed_page"),
                    normalized_text=item["normalized_text"],
                    review_status=ReviewStatus(item["review_status"]),
                    is_published=bool(item["is_published"]),
                    region_type=item.get("region_type", "text"),
                    x=float(item.get("x", 0)),
                    y=float(item.get("y", 0)),
                    width=float(item.get("width", 0)),
                    height=float(item.get("height", 0)),
                )
                for item in data["fragments"]
            ),
            audio=tuple(
                AudioEntry(
                    UUID(item["id"]),
                    UUID(item["media_asset_id"]),
                    UUID(item["activity_id"]),
                    int(item["unit_number"]),
                    item["object_key"],
                    item["bucket"],
                    int(item["track_number"]),
                    item["mime_type"],
                    int(item["size_bytes"]),
                    item["checksum"],
                )
                for item in data["audio"]
            ),
        )

    @classmethod
    def load(cls, path: Path) -> "SeedManifest":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
