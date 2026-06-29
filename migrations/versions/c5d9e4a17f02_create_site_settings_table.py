"""create site_settings table

Revision ID: c5d9e4a17f02
Revises: a3f8c2e91b4d
Create Date: 2026-06-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5d9e4a17f02'
down_revision = 'a3f8c2e91b4d'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'site_settings' not in inspector.get_table_names():
        op.create_table(
            'site_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('hero_image', sa.String(length=300), nullable=True),
            sa.Column('hero_image_size_kb', sa.Float(), nullable=True),
            sa.Column('hero_image_uploaded_at', sa.DateTime(), nullable=True),
            sa.Column('testimonial_image', sa.String(length=300), nullable=True),
            sa.Column('testimonial_image_size_kb', sa.Float(), nullable=True),
            sa.Column('testimonial_image_uploaded_at', sa.DateTime(), nullable=True),
            sa.Column('cta_image', sa.String(length=300), nullable=True),
            sa.Column('cta_image_size_kb', sa.Float(), nullable=True),
            sa.Column('cta_image_uploaded_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'site_settings' in inspector.get_table_names():
        op.drop_table('site_settings')