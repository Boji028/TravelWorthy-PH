"""add admin_response and responded_at to contact_messages

Revision ID: a1c5e9f3b7d2
Revises: 3cee47dfc5ac
Create Date: 2026-07-17 02:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c5e9f3b7d2'
down_revision = '3cee47dfc5ac'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('contact_messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_response', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('responded_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('contact_messages', schema=None) as batch_op:
        batch_op.drop_column('responded_at')
        batch_op.drop_column('admin_response')
