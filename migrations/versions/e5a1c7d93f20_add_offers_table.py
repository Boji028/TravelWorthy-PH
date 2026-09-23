"""add offers table

Offers are admin-managed group deals (corporate incentives, team building,
field trips) that sit outside packages and visa.

Revision ID: e5a1c7d93f20
Revises: c4e8f2a61b90
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa


revision = 'e5a1c7d93f20'
down_revision = 'c4e8f2a61b90'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'offers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='Other'),
        sa.Column('summary', sa.String(length=300), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image', sa.String(length=300), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('min_pax', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('offers')
