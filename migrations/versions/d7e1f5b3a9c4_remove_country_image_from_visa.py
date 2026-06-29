"""remove country_image columns from visa_countries

Revision ID: d7e1f5b3a9c4
Revises: c5d9e4a17f02
Create Date: 2026-06-23 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7e1f5b3a9c4'
down_revision = 'c5d9e4a17f02'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('visa_countries')}

    with op.batch_alter_table('visa_countries') as batch_op:
        if 'country_image' in existing_columns:
            batch_op.drop_column('country_image')
        if 'country_image_size_kb' in existing_columns:
            batch_op.drop_column('country_image_size_kb')
        if 'country_image_uploaded_at' in existing_columns:
            batch_op.drop_column('country_image_uploaded_at')


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('visa_countries')}

    with op.batch_alter_table('visa_countries') as batch_op:
        if 'country_image' not in existing_columns:
            batch_op.add_column(sa.Column('country_image', sa.String(length=300), nullable=True))
        if 'country_image_size_kb' not in existing_columns:
            batch_op.add_column(sa.Column('country_image_size_kb', sa.Float(), nullable=True))
        if 'country_image_uploaded_at' not in existing_columns:
            batch_op.add_column(sa.Column('country_image_uploaded_at', sa.DateTime(), nullable=True))