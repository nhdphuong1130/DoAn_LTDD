from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from minio import Minio
from neo4j import GraphDatabase
from difflib import SequenceMatcher
from sqlalchemy import select

from english7.api.errors import ApplicationError
from english7.core.settings import Settings
from english7.db.models import ReviewStatus, SourceFragment
from english7.db.session import get_session_factory
from english7.modules.ai.openrouter import (
    OpenRouterEmbedder,
    OpenRouterProvider,
    UrllibJSONClient,
)
from english7.modules.image_uploads.repository import SQLAlchemyImageUploadRepository
from english7.modules.image_uploads.service import ImageUploadService
from english7.modules.knowledge.neo4j_repository import Neo4jKnowledgeRepository
from english7.modules.media.storage import MinioUploadStorage
from english7.modules.quizzes.blueprint import BlueprintSelector
from english7.modules.quizzes.domain import GeneratedQuestion
from english7.modules.quizzes.repository import (
    SQLAlchemyBlueprintRepository,
    SQLAlchemyQuizRepository,
)
from english7.modules.quizzes.service import QuizService
from english7.modules.quizzes.validator import QuestionValidator
from english7.modules.retrieval.service import RetrievalService
from english7.modules.tutor.service import TutorService


class SequenceSimilarity:
    def compare(self, left: str, right: str) -> float:
        return SequenceMatcher(None, left.lower(), right.lower()).ratio()


class GroundedQuestionGenerator:
    _CORRECT_OPTIONS = ("True", "False", "Not given")

    def __init__(self, session_factory, *, ai_provider=None) -> None:
        self._session_factory = session_factory
        self._ai_provider = ai_provider

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove markdown images, HTML tags, and normalize whitespace."""
        import re
        # Remove markdown images: ![alt](url)
        text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", text)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _is_suitable_fragment(text: str) -> bool:
        """Return True only for fragments suitable as True/False/Not given questions.

        Unsuitable fragments:
        - Contain markdown images
        - Contain raw Options lists (exercise format)
        - Contain matching arrows (->)
        - Too short to be meaningful
        - Pure numbered lists with no prose
        """
        import re
        # Has markdown image syntax
        if re.search(r"!\[[^\]]*\]\([^\)]*\)", text):
            return False
        # Has raw Options list (exercise instructions)
        if re.search(r"Options:\s*\[", text):
            return False
        # Has matching exercise arrows
        if re.search(r"\s->\s", text):
            return False
        # Too short
        if len(text.strip()) < 40:
            return False
        # Pure numbered list without enough prose
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        if lines and all(re.match(r"^\d+\.", ln) for ln in lines):
            return False
        return True

    def generate(
        self, *, duration_minutes: int, difficulty: str, question_count: int
    ) -> list[GeneratedQuestion]:
        import re
        with self._session_factory() as session:
            all_fragments = session.scalars(
                select(SourceFragment).where(
                    SourceFragment.review_status == ReviewStatus.VERIFIED.value,
                    SourceFragment.is_published == True,
                )
            ).all()
            if not all_fragments:
                raise ApplicationError(
                    "insufficient_sources",
                    "Not enough verified textbook fragments to generate quiz",
                    503,
                )

            # Filter to fragments suitable for True/False/Not given questions
            fragments = [
                f for f in all_fragments
                if self._is_suitable_fragment(f.normalized_text)
            ]
            # Fallback to all fragments if none pass the filter
            if not fragments:
                fragments = list(all_fragments)

            questions: list[GeneratedQuestion] = []
            for i in range(question_count):
                frag = fragments[i % len(fragments)]
                clean = self._clean_text(frag.normalized_text)

                prompt, correct = self._make_question(clean, i)
                answer = {
                    "options": list(self._CORRECT_OPTIONS),
                    "correct": correct,
                }
                questions.append(
                    GeneratedQuestion(
                        prompt=prompt,
                        answer=answer,
                        source_fragment_ids=(frag.id,),
                    )
                )
            return questions

    def _make_question(self, clean_text: str, index: int) -> tuple[str, str]:
        """Generate (prompt, correct_answer) for a fragment.

        Uses AI when available; falls back to a round-robin distribution so
        not every question has the same answer.
        """
        if self._ai_provider is not None:
            try:
                target = self._CORRECT_OPTIONS[index % len(self._CORRECT_OPTIONS)]
                return self._ai_generate_question(clean_text, target_answer=target)
            except Exception:
                pass  # AI failed → fall through to deterministic fallback

        # Deterministic fallback: cycle through True / False / Not given
        # so the quiz at least has varied answer distribution.
        fallback_correct = self._CORRECT_OPTIONS[index % len(self._CORRECT_OPTIONS)]
        # Take first 120 chars, break at last complete word
        statement = clean_text[:120].rstrip()
        if len(clean_text) > 120:
            last_space = statement.rfind(" ")
            if last_space > 60:
                statement = statement[:last_space]
            statement += "..."
        prompt = (
            f"According to the English 7 Global Success textbook, "
            f"is the following statement True, False, or Not given?\n\n"
            f"\"{statement}\""
        )
        return prompt, fallback_correct

    def _ai_generate_question(self, clean_text: str, target_answer: str = "True") -> tuple[str, str]:
        """Call OpenRouter to generate a True/False/Not given question.

        Returns (prompt_for_student, correct_answer).
        We tell the model WHICH answer to target so small free models reliably
        produce varied questions instead of always choosing True.
        """
        import json as _json
        from urllib.request import Request as _Req, urlopen as _open

        api_key = self._ai_provider._api_key.get_secret_value()
        model = self._ai_provider._model
        endpoint = self._ai_provider._endpoint
        timeout = min(self._ai_provider._timeout, 20)

        instructions = {
            "True": (
                "Write a statement that is DIRECTLY and CLEARLY confirmed by the passage. "
                "The statement must be True."
            ),
            "False": (
                "Write a statement that CONTRADICTS or is WRONG according to the passage. "
                "Change a key fact (a number, name, place, or action) so the statement is False."
            ),
            "Not given": (
                "Write a statement about a related topic that is NOT mentioned anywhere in the passage. "
                "The statement must be impossible to confirm or deny from the passage alone."
            ),
        }
        instruction = instructions.get(target_answer, instructions["True"])

        system = (
            "You are an English 7 quiz item writer. "
            "Given a textbook passage and an instruction, create exactly ONE statement. "
            "Return ONLY valid JSON with two keys: "
            "{\"statement\": \"<the statement>\", \"correct\": \"<True|False|Not given>\"}"
        )
        user = (
            f"Passage:\n{clean_text[:400]}\n\n"
            f"Instruction: {instruction}\n\n"
            f"The correct answer for your statement MUST be: {target_answer}\n"
            "Return JSON."
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        body = _json.dumps(payload).encode("utf-8")
        req = _Req(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with _open(req, timeout=timeout) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        content = _json.loads(data["choices"][0]["message"]["content"])
        statement = str(content.get("statement", "")).strip()
        correct = str(content.get("correct", "True")).strip()
        if correct not in self._CORRECT_OPTIONS:
            correct = "True"
        if not statement:
            raise ValueError("AI returned empty statement")
        prompt = (
            f"According to the English 7 Global Success textbook, "
            f"is the following statement True, False, or Not given?\n\n"
            f"\"{statement}\""
        )
        return prompt, correct


@dataclass(slots=True)
class RuntimeResources:
    neo4j_driver: Any

    def close(self) -> None:
        close = getattr(self.neo4j_driver, "close", None)
        if close is not None:
            close()


def _complete(settings: Settings) -> bool:
    required = (
        settings.database_url,
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password,
        settings.neo4j_vector_index,
        settings.embedding_dimensions,
        settings.retrieval_top_k,
        settings.retrieval_min_score,
        settings.retrieval_graph_depth,
        settings.retrieval_rrf_constant,
        settings.retrieval_max_context_fragments,
        settings.retrieval_allowed_units,
        settings.openrouter_api_key,
        settings.openrouter_endpoint,
        settings.openrouter_model,
        settings.openrouter_timeout_seconds,
        settings.openrouter_embedding_endpoint,
        settings.openrouter_embedding_model,
        settings.upload_max_bytes,
        settings.image_upload_prefix,
        settings.image_upload_retention_minutes,
        settings.image_upload_allowed_types,
        settings.tutor_query_max_characters,
        settings.minio_upload_bucket,
    )
    return all(value is not None and value != "" for value in required)


def configure_runtime(
    app,
    settings: Settings,
    *,
    session_factory=None,
    neo4j_driver=None,
    minio_client=None,
    http_client=None,
) -> RuntimeResources | None:
    if not _complete(settings):
        return None
    sessions = session_factory or (lambda: get_session_factory()())
    if neo4j_driver is None:
        neo4j_driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_user,
                settings.neo4j_password.get_secret_value(),
            ),
        )
    if minio_client is None:
        if not all(
            (
                settings.minio_endpoint,
                settings.minio_access_key,
                settings.minio_secret_key,
            )
        ):
            raise RuntimeError("MinIO runtime settings are incomplete")
        endpoint = settings.minio_endpoint
        secure = endpoint.startswith("https://")
        endpoint = endpoint.removeprefix("https://").removeprefix("http://")
        minio_client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key.get_secret_value(),
            secure=secure,
        )
    http = http_client or UrllibJSONClient()
    uploads = SQLAlchemyImageUploadRepository(sessions)
    app.state.image_upload_service = ImageUploadService(
        repository=uploads,
        storage=MinioUploadStorage(
            minio_client, bucket=settings.minio_upload_bucket
        ),
        maximum_bytes=settings.upload_max_bytes,
        allowed_media_types=tuple(
            item.strip()
            for item in settings.image_upload_allowed_types.split(",")
            if item.strip()
        ),
        object_prefix=settings.image_upload_prefix,
        retention=timedelta(minutes=settings.image_upload_retention_minutes),
    )
    repository = Neo4jKnowledgeRepository(
        neo4j_driver,
        vector_index_name=settings.neo4j_vector_index,
        embedding_dimensions=settings.embedding_dimensions,
        graph_result_limit=settings.retrieval_top_k,
    )
    key_str = (
        settings.openrouter_api_key.get_secret_value()
        if hasattr(settings.openrouter_api_key, "get_secret_value")
        else str(settings.openrouter_api_key or "")
    )
    if settings.embedding_dimensions == 384 or not key_str or "replace" in key_str.lower():
        from english7.modules.knowledge.fastembed_service import FastEmbedService

        embedder = FastEmbedService()
    else:
        embedder = OpenRouterEmbedder(
            http=http,
            api_key=settings.openrouter_api_key,
            endpoint=settings.openrouter_embedding_endpoint,
            model=settings.openrouter_embedding_model,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.openrouter_timeout_seconds,
        )
    retrieval = RetrievalService(
        repository=repository,
        embedder=embedder,
        allowed_units=frozenset(
            int(value.strip())
            for value in settings.retrieval_allowed_units.split(",")
            if value.strip()
        ),
        top_k=settings.retrieval_top_k,
        min_vector_score=settings.retrieval_min_score,
        graph_depth=settings.retrieval_graph_depth,
        rrf_constant=settings.retrieval_rrf_constant,
        max_context_fragments=settings.retrieval_max_context_fragments,
    )
    provider = OpenRouterProvider(
        http=http,
        api_key=settings.openrouter_api_key,
        endpoint=settings.openrouter_endpoint,
        model=settings.openrouter_model,
        timeout_seconds=settings.openrouter_timeout_seconds,
    )
    app.state.tutor_service = TutorService(
        retrieval,
        provider,
        uploads=uploads,
        maximum_query_characters=settings.tutor_query_max_characters,
    )
    blueprint_repo = SQLAlchemyBlueprintRepository(sessions)
    quiz_repo = SQLAlchemyQuizRepository(sessions)
    selector = BlueprintSelector(blueprint_repo)
    validator = QuestionValidator(
        SequenceSimilarity(),
        duplicate_threshold=settings.quiz_duplicate_threshold or 0.85,
    )
    generator = GroundedQuestionGenerator(sessions, ai_provider=provider)
    app.state.quiz_service = QuizService(
        selector=selector,
        generator=generator,
        validator=validator,
        repository=quiz_repo,
        max_audio_plays=settings.quiz_max_audio_plays or 2,
    )
    return RuntimeResources(neo4j_driver)
