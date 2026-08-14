"""create market_prices table

Revision ID: 9c3d7e1b4a6f
Revises: 7a1c2f4e9d5b
Create Date: 2026-07-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9c3d7e1b4a6f'
down_revision: Union[str, Sequence[str], None] = '7a1c2f4e9d5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'market_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crop', sa.String(length=50), nullable=False),
        sa.Column('dam_commodity_id', sa.Integer(), nullable=False),
        sa.Column('dam_commodity_name', sa.String(length=255), nullable=False),
        sa.Column('division', sa.String(length=100), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('market', sa.String(length=150), nullable=True),
        sa.Column('price_type', sa.String(length=20), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('min_price', sa.Float(), nullable=False),
        sa.Column('max_price', sa.Float(), nullable=False),
        sa.Column('avg_price', sa.Float(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('price_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('source_url', sa.String(length=255), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_market_prices_crop'), 'market_prices', ['crop'], unique=False)
    op.create_index(op.f('ix_market_prices_dam_commodity_id'), 'market_prices', ['dam_commodity_id'], unique=False)
    op.create_index(op.f('ix_market_prices_district'), 'market_prices', ['district'], unique=False)
    op.create_index(op.f('ix_market_prices_price_date'), 'market_prices', ['price_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_market_prices_price_date'), table_name='market_prices')
    op.drop_index(op.f('ix_market_prices_district'), table_name='market_prices')
    op.drop_index(op.f('ix_market_prices_dam_commodity_id'), table_name='market_prices')
    op.drop_index(op.f('ix_market_prices_crop'), table_name='market_prices')
    op.drop_table('market_prices')
