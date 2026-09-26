"""add downpayment to tour packages

Revision ID: c6d2a8e4f193
Revises: a3c9e5f17b42
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa


revision = 'c6d2a8e4f193'
down_revision = 'a3c9e5f17b42'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('downpayment', sa.String(length=200), nullable=True))


def downgrade():
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        batch_op.drop_column('downpayment')
