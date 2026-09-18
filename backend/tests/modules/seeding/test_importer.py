from dataclasses import replace
from hashlib import sha256
from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.db.models import ReviewStatus
from english7.modules.seeding.importer import SeedImporter
from english7.modules.seeding.manifest import (
    ActivityEntry,
    AudioEntry,
    FragmentEntry,
    SeedManifest,
    SectionEntry,
    SourceEntry,
    TextbookEntry,
    UnitEntry,
)


class FakeSeedRepository:
    def __init__(self):
        self.packages = {}

    def apply(self, manifest):
        created = manifest.package_id not in self.packages
        self.packages.setdefault(manifest.package_id, manifest)
        return created


class FakeStorage:
    def __init__(self, existing):
        self.existing = set(existing)

    def exists(self, object_key):
        return object_key in self.existing


def manifest(source_bytes=b"unit-one-two"):
    package_id = uuid4()
    textbook_id = uuid4()
    source_id = uuid4()
    section_id = uuid4()
    activity_id = uuid4()
    return SeedManifest(
        schema_version=1,
        package_id=package_id,
        textbook=TextbookEntry(textbook_id, "English 7 Global Success"),
        source=SourceEntry(
            id=source_id,
            filename="english-7.pdf",
            object_key="sources/english-7.pdf",
            sha256=sha256(source_bytes).hexdigest(),
            page_count=142,
            ingestion_version="test-v1",
        ),
        units=(UnitEntry(uuid4(), 1, "Hobbies", 10, 18),),
        sections=(
            SectionEntry(section_id, 1, "Getting Started", "lesson", 1),
        ),
        activities=(
            ActivityEntry(activity_id, section_id, "1", "reading", "Read"),
        ),
        fragments=(
            FragmentEntry(
                uuid4(),
                source_id,
                activity_id,
                1,
                12,
                10,
                "My hobby is collecting dolls.",
                ReviewStatus.VERIFIED,
                True,
            ),
        ),
        audio=(
            AudioEntry(
                uuid4(),
                uuid4(),
                activity_id,
                1,
                "audio/unit1-track1.mp3",
                "english7-media",
                1,
                "audio/mpeg",
                1024,
                "audio-checksum",
            ),
        ),
    )


def test_importing_same_manifest_twice_is_idempotent() -> None:
    item = manifest()
    repository = FakeSeedRepository()
    importer = SeedImporter(
        repository, FakeStorage({item.audio[0].object_key}), {1}, {1, 2}
    )

    first = importer.import_manifest(item, b"unit-one-two")
    second = importer.import_manifest(item, b"unit-one-two")

    assert first.created is True
    assert second.created is False
    assert len(repository.packages) == 1


def test_rejects_mismatched_source_hash() -> None:
    item = manifest()
    importer = SeedImporter(
        FakeSeedRepository(), FakeStorage({item.audio[0].object_key}), {1}, {1, 2}
    )

    with pytest.raises(ApplicationError) as captured:
        importer.import_manifest(item, b"different-source")

    assert captured.value.code == "seed_source_hash_mismatch"


def test_rejects_missing_audio_object_key() -> None:
    item = manifest()

    with pytest.raises(ApplicationError) as captured:
        SeedImporter(FakeSeedRepository(), FakeStorage(set()), {1}, {1, 2}).import_manifest(
            item, b"unit-one-two"
        )

    assert captured.value.code == "seed_audio_missing"


def test_rejects_fragment_outside_source_and_unit_page_bounds() -> None:
    item = manifest()
    invalid_fragment = replace(item.fragments[0], pdf_page=200)
    item = replace(item, fragments=(invalid_fragment,))

    with pytest.raises(ApplicationError) as captured:
        SeedImporter(
            FakeSeedRepository(), FakeStorage({item.audio[0].object_key}), {1}, {1, 2}
        ).import_manifest(item, b"unit-one-two")

    assert captured.value.code == "seed_page_out_of_bounds"


def test_rejects_published_fragment_that_is_not_verified() -> None:
    item = manifest()
    invalid_fragment = replace(
        item.fragments[0], review_status=ReviewStatus.DRAFT, is_published=True
    )
    item = replace(item, fragments=(invalid_fragment,))

    with pytest.raises(ApplicationError) as captured:
        SeedImporter(
            FakeSeedRepository(), FakeStorage({item.audio[0].object_key}), {1}, {1, 2}
        ).import_manifest(item, b"unit-one-two")

    assert captured.value.code == "seed_unverified_publication"
