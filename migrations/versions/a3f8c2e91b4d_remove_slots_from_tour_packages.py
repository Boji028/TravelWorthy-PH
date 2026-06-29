"""remove max_slots and available_slots from tour_packages

Revision ID: a3f8c2e91b4d
Revises: b7e4f1a9c3d2
Create Date: 2026-06-22 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f8c2e91b4d'
down_revision = 'b7e4f1a9c3d2'
branch_labels = None
depends_on = None


def _existing_columns():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns('tour_packages')}


def upgrade():
    existing = _existing_columns()
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        if 'max_slots' in existing:
            batch_op.drop_column('max_slots')
        if 'available_slots' in existing:
            batch_op.drop_column('available_slots')


def downgrade():
    existing = _existing_columns()
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        if 'available_slots' not in existing:
            batch_op.add_column(sa.Column('available_slots', sa.Integer(), nullable=False, server_default='20'))
        if 'max_slots' not in existing:
            batch_op.add_column(sa.Column('max_slots', sa.Integer(), nullable=False, server_default='20'))