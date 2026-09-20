from dataclasses import dataclass, replace

from english7.modules.knowledge.contracts import GraphBuildRecord
from english7.modules.knowledge.domain import GraphBuildStatus
from english7.modules.knowledge.graph_builder import ProjectionEmbeddingBuilder
from english7.modules.knowledge.neo4j_repository import Neo4jBuildReport


class GraphBuildValidationError(RuntimeError):
    def __init__(self, report: Neo4jBuildReport) -> None:
        self.report = report
        super().__init__("Knowledge graph candidate failed validation")


@dataclass(frozen=True, slots=True)
class GraphBuildResult:
    build: GraphBuildRecord
    validation_report: Neo4jBuildReport | None
    reused_active_build: bool = False


def _failure_code(error: Exception, stage: str) -> str:
    if isinstance(error, GraphBuildValidationError):
        return "validation_failed"
    if stage in {"index", "validation"} and isinstance(
        error, (TimeoutError, ConnectionError)
    ):
        return "index_unavailable"
    if stage == "embedding":
        return "embedding_failed"
    return "graph_build_failed"


class KnowledgeGraphBuildService:
    def __init__(
        self,
        sql_repository,
        neo4j_repository,
        graph_builder: ProjectionEmbeddingBuilder,
        *,
        index_timeout_seconds: float,
    ) -> None:
        if index_timeout_seconds <= 0:
            raise ValueError("Index timeout must be positive")
        self._sql = sql_repository
        self._neo4j = neo4j_repository
        self._graph_builder = graph_builder
        self._index_timeout_seconds = index_timeout_seconds

    def build(self, ontology_version: str) -> GraphBuildResult:
        if not ontology_version.strip():
            raise ValueError("Ontology version is required")
        projection = self._sql.load_projection(ontology_version)
        build = self._sql.start_build(projection, self._graph_builder.identity)
        if build.status is GraphBuildStatus.ACTIVE:
            return GraphBuildResult(build, None, reused_active_build=True)

        stage = "embedding"
        try:
            vectors = self._graph_builder.embed(projection)
            stage = "projection"
            self._neo4j.prepare_build(build.id, self._graph_builder.identity)
            self._neo4j.write_projection(build.id, projection, vectors)
            stage = "index"
            self._neo4j.ensure_indexes(build.id, self._graph_builder.identity)
            self._neo4j.wait_until_online(
                build.id, timeout_seconds=self._index_timeout_seconds
            )
            stage = "validation"
            report = self._neo4j.validate_build(
                build.id,
                projection.expected_counts,
                dimensions=self._graph_builder.identity.dimensions,
            )
            if not report.valid:
                raise GraphBuildValidationError(report)
            stage = "activation"
            self._sql.mark_validated(build.id, report.to_dict())
            self._sql.activate_build(build.id)
            active = replace(
                build,
                status=GraphBuildStatus.ACTIVE,
                actual_counts=report.counts,
                validation_report=report.to_dict(),
            )
            return GraphBuildResult(active, report)
        except Exception as error:
            self._sql.mark_failed(build.id, _failure_code(error, stage))
            raise
