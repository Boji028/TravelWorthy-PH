"""add inquiry constraints and email index

Revision ID: a061d874a03c
Revises: db964fb36066
Create Date: 2026-06-08 19:33:03.959534

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a061d874a03c'
down_revision = 'db964fb36066'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE inquiries
        SET reference_number = 'INQ-' || UPPER(SUBSTRING(MD5(RANDOM()::TEXT || id::TEXT), 1, 5))
        WHERE reference_number IS NULL
    """)

    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.alter_column('reference_number',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
        batch_op.create_index(batch_op.f('ix_inquiries_email'), ['email'], unique=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('email_verified',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('false'))
        batch_op.create_index(batch_op.f('ix_users_email_verified'), ['email_verified'], unique=False)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email_verified'))
        batch_op.alter_column('email_verified',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('false'))

    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_inquiries_email'))
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('reference_number',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)