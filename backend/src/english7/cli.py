import argparse
from pathlib import Path
from uuid import UUID

from english7.db.session import get_session_factory
from english7.modules.seeding.importer import SeedImporter
from english7.modules.seeding.manifest import SeedManifest
from english7.modules.seeding.repository import SQLAlchemySeedRepository


class FileObjectCatalog:
    def __init__(self, listing_path: Path) -> None:
        self._keys = {
            line.strip()
            for line in listing_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    def exists(self, object_key: str) -> bool:
        return object_key in self._keys


def _repository() -> SQLAlchemySeedRepository:
    return SQLAlchemySeedRepository(lambda: get_session_factory()())


def import_seed(args: argparse.Namespace) -> None:
    manifest = SeedManifest.load(args.manifest)
    importer = SeedImporter(
        _repository(),
        FileObjectCatalog(args.audio_object_list),
        set(args.supported_schema_version),
        set(args.allowed_unit),
    )
    result = importer.import_manifest(manifest, args.source.read_bytes())
    print(
        f"package={result.package_id} created={str(result.created).lower()} "
        f"fragments={result.fragment_count} audio={result.audio_count}"
    )


def export_seed(args: argparse.Namespace) -> None:
    manifest = _repository().get_manifest(args.package_id)
    if manifest is None:
        raise SystemExit("Seed package was not found")
    args.output.write_text(manifest.to_json() + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="english7")
    commands = parser.add_subparsers(required=True)

    importer = commands.add_parser("import-seed")
    importer.add_argument("--manifest", type=Path, required=True)
    importer.add_argument("--source", type=Path, required=True)
    importer.add_argument("--audio-object-list", type=Path, required=True)
    importer.add_argument(
        "--supported-schema-version", type=int, action="append", required=True
    )
    importer.add_argument("--allowed-unit", type=int, action="append", required=True)
    importer.set_defaults(handler=import_seed)

    exporter = commands.add_parser("export-seed")
    exporter.add_argument("--package-id", type=UUID, required=True)
    exporter.add_argument("--output", type=Path, required=True)
    exporter.set_defaults(handler=export_seed)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
