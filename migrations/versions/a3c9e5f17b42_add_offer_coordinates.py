"""add latitude and longitude to offers

Revision ID: a3c9e5f17b42
Revises: f7b2d4e81a36
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3c9e5f17b42'
down_revision = 'f7b2d4e81a36'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
