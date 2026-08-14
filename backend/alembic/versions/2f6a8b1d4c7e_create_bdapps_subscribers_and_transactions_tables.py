"""create bdapps subscribers and transactions tables

Revision ID: 2f6a8b1d4c7e
Revises: 9c3d7e1b4a6f
Create Date: 2026-07-25 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2f6a8b1d4c7e'
down_revision: Union[str, Sequence[str], None] = '9c3d7e1b4a6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'bdapps_subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('msisdn', sa.String(length=20), nullable=False),
        sa.Column('subscription_status', sa.String(length=20), nullable=False),
        sa.Column('last_event_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bdapps_subscribers_msisdn'), 'bdapps_subscribers', ['msisdn'], unique=True)

    op.create_table(
        'bdapps_charge_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('msisdn', sa.String(length=20), nullable=False),
        sa.Column('external_trx_id', sa.String(length=64), nullable=False),
        sa.Column('internal_trx_id', sa.String(length=64), nullable=True),
        sa.Column('reference_id', sa.String(length=64), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.String(length=20), nullable=True),
        sa.Column('status_detail', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bdapps_charge_transactions_msisdn'), 'bdapps_charge_transactions', ['msisdn'], unique=False)
    op.create_index(
        op.f('ix_bdapps_charge_transactions_external_trx_id'),
        'bdapps_charge_transactions',
        ['external_trx_id'],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_bdapps_charge_transactions_external_trx_id'), table_name='bdapps_charge_transactions')
    op.drop_index(op.f('ix_bdapps_charge_transactions_msisdn'), table_name='bdapps_charge_transactions')
    op.drop_table('bdapps_charge_transactions')
    op.drop_index(op.f('ix_bdapps_subscribers_msisdn'), table_name='bdapps_subscribers')
    op.drop_table('bdapps_subscribers')
