from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from english7.api.errors import ApplicationError
from english7.db.models import ReviewStatus
from english7.modules.seeding.manifest import SeedManifest


class SeedRepository(Protocol):
    def apply(self, manifest: SeedManifest) -> bool: ...


class ObjectCatalog(Protocol):
    def exists(self, object_key: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class ImportResult:
    package_id: str
    created: bool
    fragment_count: int
    audio_count: int


class SeedImporter:
    def __init__(
        self,
        repository: SeedRepository,
        storage: ObjectCatalog,
        supported_schema_versions: set[int],
        allowed_units: set[int],
    ) -> None:
        if not supported_schema_versions:
            raise ValueError("At least one seed schema version must be supported")
        if not allowed_units:
            raise ValueError("At least one Unit must be allowed")
        self._repository = repository
        self._storage = storage
        self._versions = supported_schema_versions
        self._allowed_units = allowed_units

    def _validate(self, manifest: SeedManifest, source_bytes: bytes) -> None:
        if manifest.schema_version not in self._versions:
            raise ApplicationError(
                "seed_schema_unsupported", "Seed schema version is unsupported", 422
            )
        if sha256(source_bytes).hexdigest() != manifest.source.sha256:
            raise ApplicationError(
                "seed_source_hash_mismatch", "Source document hash does not match", 422
            )
        units = {unit.number: unit for unit in manifest.units}
        if not units or not set(units).issubset(self._allowed_units):
            raise ApplicationError(
                "seed_unit_out_of_scope", "Seed package contains an unsupported Unit", 422
            )
        for unit in units.values():
            if (
                unit.pdf_page_start < 0
                or unit.pdf_page_start > unit.pdf_page_end
                or unit.pdf_page_end >= manifest.source.page_count
            ):
                raise ApplicationError(
                    "seed_page_out_of_bounds", "Unit page bounds are invalid", 422
                )
        section_ids = {section.id for section in manifest.sections}
        if any(section.unit_number not in units for section in manifest.sections):
            raise ApplicationError(
                "seed_hierarchy_invalid", "Section hierarchy is invalid", 422
            )
        activity_ids = {item.id for item in manifest.activities}
        if any(item.section_id not in section_ids for item in manifest.activities):
            raise ApplicationError(
                "seed_hierarchy_invalid", "Activity hierarchy is invalid", 422
            )
        for fragment in manifest.fragments:
            unit = units.get(fragment.unit_number)
            if (
                unit is None
                or fragment.pdf_page < unit.pdf_page_start
                or fragment.pdf_page > unit.pdf_page_end
                or fragment.pdf_page >= manifest.source.page_count
                or fragment.source_document_id != manifest.source.id
                or (
                    fragment.activity_id is not None
                    and fragment.activity_id not in activity_ids
                )
            ):
                raise ApplicationError(
                    "seed_page_out_of_bounds",
                    "Fragment page is outside source or Unit bounds",
                    422,
                )
            if (
                fragment.is_published
                and fragment.review_status is not ReviewStatus.VERIFIED
            ):
                raise ApplicationError(
                    "seed_unverified_publication",
                    "Only verified fragments may be published",
                    422,
                )
        for audio in manifest.audio:
            if audio.activity_id not in activity_ids or audio.unit_number not in units:
                raise ApplicationError(
                    "seed_audio_mapping_invalid", "Audio mapping is invalid", 422
                )
            if not self._storage.exists(audio.object_key):
                raise ApplicationError(
                    "seed_audio_missing", "A referenced audio object is missing", 422
                )

    def import_manifest(
        self, manifest: SeedManifest, source_bytes: bytes
    ) -> ImportResult:
        self._validate(manifest, source_bytes)
        created = self._repository.apply(manifest)
        return ImportResult(
            str(manifest.package_id),
            created,
            len(manifest.fragments),
            len(manifest.audio),
        )
