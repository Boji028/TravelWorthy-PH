"""add image to itinerary_days

Revision ID: a7c2e9f14b60
Revises: cc1e21563818
Create Date: 2026-09-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7c2e9f14b60'
down_revision = 'cc1e21563818'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('itinerary_days', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table('itinerary_days', schema=None) as batch_op:
        batch_op.drop_column('image')
