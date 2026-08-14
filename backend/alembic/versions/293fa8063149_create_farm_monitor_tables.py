"""create alerts and trace_log tables

Revision ID: 293fa8063149
Revises: c4e8a1f6b9d2
Create Date: 2026-07-24 18:52:00.119350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '293fa8063149'
down_revision: Union[str, Sequence[str], None] = 'c4e8a1f6b9d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # `farms` and `plans` are already created by c4e8a1f6b9d2 (conversation
    # agent's migration, same schema) — this revision only adds the
    # monitor agent's own tables on top.
    op.create_table('alerts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('farm_id', sa.Integer(), nullable=False),
    sa.Column('trigger_reason', sa.String(length=255), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_created_at'), 'alerts', ['created_at'], unique=False)
    op.create_index(op.f('ix_alerts_farm_id'), 'alerts', ['farm_id'], unique=False)
    op.create_table('trace_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('farm_id', sa.Integer(), nullable=True),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('node_name', sa.String(length=100), nullable=False),
    sa.Column('tool_name', sa.String(length=100), nullable=True),
    sa.Column('params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trace_log_created_at'), 'trace_log', ['created_at'], unique=False)
    op.create_index(op.f('ix_trace_log_farm_id'), 'trace_log', ['farm_id'], unique=False)
    op.create_index(op.f('ix_trace_log_source'), 'trace_log', ['source'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_trace_log_source'), table_name='trace_log')
    op.drop_index(op.f('ix_trace_log_farm_id'), table_name='trace_log')
    op.drop_index(op.f('ix_trace_log_created_at'), table_name='trace_log')
    op.drop_table('trace_log')
    op.drop_index(op.f('ix_alerts_farm_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_created_at'), table_name='alerts')
    op.drop_table('alerts')
