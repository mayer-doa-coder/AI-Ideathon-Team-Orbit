"""create kb_chunks table

Revision ID: b7c1d4e9f2a3
Revises: 93b66fc5a693
Create Date: 2026-07-24 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'b7c1d4e9f2a3'
down_revision: Union[str, Sequence[str], None] = '93b66fc5a693'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'kb_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_title', sa.String(length=255), nullable=False),
        sa.Column('crop', sa.String(length=100), nullable=True),
        sa.Column('topic', sa.String(length=255), nullable=True),
        sa.Column('section_heading', sa.String(length=255), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_kb_chunks_source_title'), 'kb_chunks', ['source_title'], unique=False)
    op.create_index(op.f('ix_kb_chunks_crop'), 'kb_chunks', ['crop'], unique=False)
    op.create_index(op.f('ix_kb_chunks_topic'), 'kb_chunks', ['topic'], unique=False)
    op.execute(
        "CREATE INDEX ix_kb_chunks_embedding_hnsw ON kb_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_kb_chunks_embedding_hnsw")
    op.drop_index(op.f('ix_kb_chunks_topic'), table_name='kb_chunks')
    op.drop_index(op.f('ix_kb_chunks_crop'), table_name='kb_chunks')
    op.drop_index(op.f('ix_kb_chunks_source_title'), table_name='kb_chunks')
    op.drop_table('kb_chunks')
