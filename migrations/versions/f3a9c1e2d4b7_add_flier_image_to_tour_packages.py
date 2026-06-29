"""add flier_image to tour_packages

Revision ID: f3a9c1e2d4b7
Revises: e2b001aab8e4
Create Date: 2026-06-16 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a9c1e2d4b7'
down_revision = 'e2b001aab8e4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('flier_image', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('flier_image_size_kb', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('flier_image_uploaded_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        batch_op.drop_column('flier_image_uploaded_at')
        batch_op.drop_column('flier_image_size_kb')
        batch_op.drop_column('flier_image')