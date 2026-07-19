"""drop contact_messages table

Revision ID: b4d8f1a6c3e7
Revises: a1c5e9f3b7d2
Create Date: 2026-07-19 02:40:00.000000

The Contact Us messaging feature was removed at the boss's request: the
public page is now reach-us details only (phone/email/office/hours), with
no form, no ContactMessage records, and no admin Contact Messages panel.
Existing messages don't need to be preserved.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4d8f1a6c3e7'
down_revision = 'a1c5e9f3b7d2'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('contact_messages')


def downgrade():
    op.create_table(
        'contact_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
