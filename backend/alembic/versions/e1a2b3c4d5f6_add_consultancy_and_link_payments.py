"""add consultation_requests table and link charge transactions to users

Revision ID: e1a2b3c4d5f6
Revises: a1b2c3d4e5f6
Create Date: 2026-07-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5f6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'bdapps_charge_transactions',
        sa.Column('user_id', sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f('ix_bdapps_charge_transactions_user_id'),
        'bdapps_charge_transactions',
        ['user_id'],
    )
    op.create_foreign_key(
        'fk_bdapps_charge_transactions_user_id_users',
        'bdapps_charge_transactions',
        'users',
        ['user_id'],
        ['id'],
    )

    op.create_table(
        'consultation_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expert_id', sa.String(length=50), nullable=False),
        sa.Column('expert_name', sa.String(length=100), nullable=False),
        sa.Column('expert_specialty', sa.String(length=100), nullable=False),
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('expert_reply', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_consultation_requests_user_id'),
        'consultation_requests',
        ['user_id'],
    )
    op.create_index(
        op.f('ix_consultation_requests_created_at'),
        'consultation_requests',
        ['created_at'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_consultation_requests_created_at'), table_name='consultation_requests')
    op.drop_index(op.f('ix_consultation_requests_user_id'), table_name='consultation_requests')
    op.drop_table('consultation_requests')

    op.drop_constraint(
        'fk_bdapps_charge_transactions_user_id_users',
        'bdapps_charge_transactions',
        type_='foreignkey',
    )
    op.drop_index(
        op.f('ix_bdapps_charge_transactions_user_id'),
        table_name='bdapps_charge_transactions',
    )
    op.drop_column('bdapps_charge_transactions', 'user_id')
