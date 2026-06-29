"""price columns to numeric

Revision ID: db964fb36066
Revises: bcd615f31c5b
Create Date: 2026-06-08 18:56:05.239053

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'db964fb36066'
down_revision = 'bcd615f31c5b'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('bookings', 'total_price',
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=12, scale=2),
        existing_nullable=False)
    op.alter_column('tour_packages', 'price',
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=12, scale=2),
        existing_nullable=False)


def downgrade():
    op.alter_column('tour_packages', 'price',
        existing_type=sa.Numeric(precision=12, scale=2),
        type_=sa.Float(),
        existing_nullable=False)
    op.alter_column('bookings', 'total_price',
        existing_type=sa.Numeric(precision=12, scale=2),
        type_=sa.Float(),
        existing_nullable=False)