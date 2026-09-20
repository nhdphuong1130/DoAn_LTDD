from argparse import Namespace
from pathlib import Path
from uuid import UUID

from english7 import cli
from english7.modules.knowledge.ontology_importer import OntologyImportResult


class SuccessfulImporter:
    def __init__(self, repository) -> None:
        pass

    def import_manifest(self, manifest) -> OntologyImportResult:
        return OntologyImportResult(
            UUID("10000000-0000-4000-8000-000000000001"),
            True,
            3,
            4,
        )


def test_import_ontology_prints_only_safe_summary(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "OntologyImporter", SuccessfulImporter)
    monkeypatch.setattr(cli, "_knowledge_repository", lambda: object())
    monkeypatch.setattr(cli.OntologyManifest, "load", lambda _path: object())

    cli.import_ontology(Namespace(manifest=Path("ontology.json")))

    assert capsys.readouterr().out == (
        "manifest=10000000-0000-4000-8000-000000000001 "
        "created=true concepts=3 assertions=4\n"
    )
