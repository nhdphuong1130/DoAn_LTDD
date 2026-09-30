"""Add private flashcard learning and speaking records without altering existing tables."""
from alembic import op
import sqlalchemy as sa

revision = '0007_learning'
down_revision = '0006_user_personal_profile'
branch_labels = None
depends_on = None

TABLES = {'flashcard_decks', 'flashcards', 'flashcard_states', 'flashcard_reviews',
          'speaking_attempts', 'speaking_preferences'}


def schema():
    """Revision-local definitions: future ORM edits cannot change this migration."""
    metadata = sa.MetaData()
    for name in ('users', 'units', 'source_fragments'):
        sa.Table(name, metadata, sa.Column('id', sa.Uuid, primary_key=True))

    def identity():
        return sa.Column('id', sa.Uuid, primary_key=True)

    def timestamps():
        return [sa.Column(name, sa.DateTime(timezone=True), nullable=False)
                for name in ('created_at', 'updated_at')]

    sa.Table('flashcard_decks', metadata,
        identity(), *timestamps(),
        sa.Column('owner_id', sa.Uuid, sa.ForeignKey('users.id'), index=True),
        sa.Column('name', sa.Unicode(200), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('unit_number', sa.Integer),
        sa.Column('unit_id', sa.Uuid, sa.ForeignKey('units.id')),
        sa.CheckConstraint("(kind = 'textbook' AND owner_id IS NULL) OR (kind = 'personal' AND owner_id IS NOT NULL)", name='ck_flashcard_deck_owner'))
    sa.Table('flashcards', metadata,
        identity(), *timestamps(),
        sa.Column('deck_id', sa.Uuid, sa.ForeignKey('flashcard_decks.id'), nullable=False, index=True),
        sa.Column('word', sa.Unicode(200), nullable=False),
        sa.Column('normalized_word', sa.Unicode(200), nullable=False),
        sa.Column('meaning', sa.Unicode(1000), nullable=False),
        sa.Column('example', sa.UnicodeText, nullable=False),
        sa.Column('notes', sa.UnicodeText, nullable=False),
        sa.Column('image_url', sa.Unicode(2048)),
        sa.Column('ipa', sa.Unicode(200)),
        sa.Column('pos', sa.Unicode(100)),
        sa.Column('source_fragment_id', sa.Uuid, sa.ForeignKey('source_fragments.id')),
        sa.Column('unit_number', sa.Integer),
        sa.Column('page', sa.Integer),
        sa.Column('audio_url', sa.Unicode(2048)),
        sa.UniqueConstraint('deck_id', 'normalized_word', name='uq_flashcard_word'))
    sa.Table('flashcard_states', metadata,
        identity(),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('card_id', sa.Uuid, sa.ForeignKey('flashcards.id'), nullable=False, index=True),
        sa.Column('difficult', sa.Boolean, nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True)),
        sa.Column('review_count', sa.Integer, nullable=False),
        sa.Column('successful_reviews', sa.Integer, nullable=False),
        sa.UniqueConstraint('user_id', 'card_id', name='uq_flashcard_state'))
    sa.Table('flashcard_reviews', metadata,
        identity(),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('card_id', sa.Uuid, sa.ForeignKey('flashcards.id'), nullable=False, index=True),
        sa.Column('request_id', sa.Uuid, nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('result', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'request_id', name='uq_flashcard_review_request'))
    sa.Table('speaking_attempts', metadata,
        identity(), *timestamps(),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('card_id', sa.Uuid, nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('voice_id', sa.String(100), nullable=False),
        sa.Column('model', sa.String(200), nullable=False),
        sa.Column('prompt', sa.UnicodeText, nullable=False),
        sa.Column('transcript', sa.UnicodeText, nullable=False),
        sa.Column('source_label', sa.UnicodeText, nullable=False),
        sa.Column('result', sa.JSON, nullable=False))
    sa.Table('speaking_preferences', metadata,
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('voice_id', sa.String(100), nullable=False))
    return metadata


def upgrade():
    metadata = schema()
    tables = [t for t in metadata.sorted_tables if t.name in TABLES]
    metadata.create_all(op.get_bind(), tables=tables, checkfirst=True)


def downgrade():
    metadata = schema()
    tables = [t for t in metadata.sorted_tables if t.name in TABLES]
    metadata.drop_all(op.get_bind(), tables=tables, checkfirst=True)
