from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from english7.db.session import get_engine


def test_initial_migration_creates_expected_tables() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")

    table_names = set(inspect(get_engine()).get_table_names())

    assert {
        "users",
        "source_documents",
        "source_fragments",
        "quiz_questions",
        "test_attempts",
        "audio_playbacks",
    } <= table_names

