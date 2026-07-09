"""add inquiry last_exported_at, make notification inquiry_id nullable

Revision ID: a7c3f9e2b1d4
Revises: c2551e8ab7aa
Create Date: 2026-07-09 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7c3f9e2b1d4'
down_revision = 'c2551e8ab7aa'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_exported_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_inquiries_last_exported_at'), ['last_exported_at'], unique=False)

    with op.batch_alter_table('inquiry_notifications', schema=None) as batch_op:
        batch_op.alter_column('inquiry_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade():
    with op.batch_alter_table('inquiry_notifications', schema=None) as batch_op:
        batch_op.alter_column('inquiry_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_inquiries_last_exported_at'))
        batch_op.drop_column('last_exported_at')
