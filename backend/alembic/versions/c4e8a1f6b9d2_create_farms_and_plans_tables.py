"""create farms and plans tables

Revision ID: c4e8a1f6b9d2
Revises: b7c1d4e9f2a3
Create Date: 2026-07-24 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c4e8a1f6b9d2'
down_revision: Union[str, Sequence[str], None] = 'b7c1d4e9f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'farms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('acres', sa.Float(), nullable=True),
        sa.Column('soil_type', sa.String(length=100), nullable=True),
        sa.Column('water_availability', sa.String(length=50), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('season', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_farms_user_id'), 'farms', ['user_id'], unique=True)

    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('selected_crop', sa.String(length=100), nullable=True),
        sa.Column('crop_candidates', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('season_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('financials', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_plans_farm_id'), 'plans', ['farm_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_plans_farm_id'), table_name='plans')
    op.drop_table('plans')
    op.drop_index(op.f('ix_farms_user_id'), table_name='farms')
    op.drop_table('farms')
