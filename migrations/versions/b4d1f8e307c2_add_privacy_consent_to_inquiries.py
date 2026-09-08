"""add privacy consent to inquiries

Revision ID: b4d1f8e307c2
Revises: a7c2e9f14b60
Create Date: 2026-09-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4d1f8e307c2'
down_revision = 'a7c2e9f14b60'
branch_labels = None
depends_on = None


def upgrade():
    # Existing rows default to false: consent was never actually collected
    # for them, so recording it as given would be untrue.
    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('privacy_consent', sa.Boolean(), nullable=False, server_default='false')
        )
        batch_op.add_column(sa.Column('privacy_consent_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.drop_column('privacy_consent_at')
        batch_op.drop_column('privacy_consent')
