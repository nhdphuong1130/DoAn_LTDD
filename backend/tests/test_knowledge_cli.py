from argparse import Namespace
from pathlib import Path
from uuid import UUID

from english7 import cli
from english7.modules.knowledge.build_service import GraphBuildResult
from english7.modules.knowledge.contracts import GraphBuildRecord
from english7.modules.knowledge.domain import GraphBuildStatus
from english7.modules.knowledge.embedding import EmbeddingIdentity
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


class FakeDriver:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class SuccessfulBuildService:
    def build(self, ontology_version: str) -> GraphBuildResult:
        assert ontology_version == "english7-v1"
        return GraphBuildResult(
            GraphBuildRecord(
                UUID("20000000-0000-4000-8000-000000000001"),
                "safe-checksum",
                ontology_version,
                GraphBuildStatus.ACTIVE,
                {"fragments": 2},
                {"fragments": 2},
                {"failures": []},
                None,
            ),
            None,
        )


def test_build_knowledge_graph_prints_safe_summary_and_closes_driver(
    monkeypatch, capsys
) -> None:
    driver = FakeDriver()
    identity = EmbeddingIdentity("fake", "model", "v1", 384, "", "", "v1")
    monkeypatch.setattr(
        cli,
        "_knowledge_build_service",
        lambda: (SuccessfulBuildService(), driver, identity),
    )

    cli.build_knowledge_graph(Namespace(ontology_version="english7-v1"))

    output = capsys.readouterr().out
    assert '"status": "active"' in output
    assert '"dimensions": 384' in output
    assert "safe-checksum" in output
    assert "password" not in output.lower()
    assert "embedding" not in output or "embedding_identity" in output
    assert driver.closed is True


def test_parser_accepts_build_knowledge_graph_command() -> None:
    args = cli.build_parser().parse_args(
        ["build-knowledge-graph", "--ontology-version", "english7-v1"]
    )

    assert args.handler is cli.build_knowledge_graph
