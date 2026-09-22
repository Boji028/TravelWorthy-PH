"""add price on request to packages

Packages without a fixed price can now be marked "price on request",
which makes the price itself optional.

Revision ID: c4e8f2a61b90
Revises: b7c3e9a15d42
Create Date: 2026-09-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'c4e8f2a61b90'
down_revision = 'b7c3e9a15d42'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        # server_default fills every existing package with "false" in the
        # same step, so adding a NOT NULL column can't fail on existing rows.
        batch_op.add_column(
            sa.Column('price_on_request', sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.alter_column('price', existing_type=sa.Numeric(precision=12, scale=2), nullable=True)


def downgrade():
    # Packages with no price can't satisfy NOT NULL again - give them 0
    # rather than deleting them.
    op.execute("UPDATE tour_packages SET price = 0 WHERE price IS NULL")
    with op.batch_alter_table('tour_packages', schema=None) as batch_op:
        batch_op.alter_column('price', existing_type=sa.Numeric(precision=12, scale=2), nullable=False)
        batch_op.drop_column('price_on_request')
