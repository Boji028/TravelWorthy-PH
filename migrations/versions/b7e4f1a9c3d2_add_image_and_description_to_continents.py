"""add image and description fields to continents

Revision ID: b7e4f1a9c3d2
Revises: f3a9c1e2d4b7
Create Date: 2026-06-21 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e4f1a9c3d2'
down_revision = 'f3a9c1e2d4b7'
branch_labels = None
depends_on = None


def _existing_columns():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns('continents')}


def upgrade():
    existing = _existing_columns()
    with op.batch_alter_table('continents', schema=None) as batch_op:
        if 'description' not in existing:
            batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        if 'image' not in existing:
            batch_op.add_column(sa.Column('image', sa.String(length=300), nullable=True))
        if 'image_size_kb' not in existing:
            batch_op.add_column(sa.Column('image_size_kb', sa.Float(), nullable=True))
        if 'image_uploaded_at' not in existing:
            batch_op.add_column(sa.Column('image_uploaded_at', sa.DateTime(), nullable=True))


def downgrade():
    existing = _existing_columns()
    with op.batch_alter_table('continents', schema=None) as batch_op:
        if 'image_uploaded_at' in existing:
            batch_op.drop_column('image_uploaded_at')
        if 'image_size_kb' in existing:
            batch_op.drop_column('image_size_kb')
        if 'image' in existing:
            batch_op.drop_column('image')
        if 'description' in existing:
            batch_op.drop_column('description')