"""create suppliers and supplier_products tables

Revision ID: 7a1c2f4e9d5b
Revises: 293fa8063149
Create Date: 2026-07-24 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7a1c2f4e9d5b'
down_revision: Union[str, Sequence[str], None] = '293fa8063149'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_suppliers_district'), 'suppliers', ['district'], unique=False)

    op.create_table(
        'supplier_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('price_bdt_per_unit', sa.Float(), nullable=False),
        sa.Column('stock_available', sa.Float(), nullable=False),
        sa.Column('delivery_days', sa.Integer(), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_supplier_products_supplier_id'), 'supplier_products', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_supplier_products_product_name'), 'supplier_products', ['product_name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_supplier_products_product_name'), table_name='supplier_products')
    op.drop_index(op.f('ix_supplier_products_supplier_id'), table_name='supplier_products')
    op.drop_table('supplier_products')
    op.drop_index(op.f('ix_suppliers_district'), table_name='suppliers')
    op.drop_table('suppliers')
