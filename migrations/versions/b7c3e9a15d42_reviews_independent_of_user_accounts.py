"""reviews and testimonials independent of user accounts

Customers no longer have accounts, so admin enters reviews directly.
Each review/testimonial now keeps its own copy of the client's name, and
user_id becomes optional.

Revision ID: b7c3e9a15d42
Revises: 4f1a00641546
Create Date: 2026-09-21

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7c3e9a15d42'
down_revision = '4f1a00641546'
branch_labels = None
depends_on = None


def upgrade():
    # 1. New columns, all optional so adding them can't fail on existing rows.
    with op.batch_alter_table('package_reviews', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reviewer_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('image', sa.String(length=500), nullable=True))

    with op.batch_alter_table('testimonials', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reviewer_name', sa.String(length=100), nullable=True))

    # 2. Copy each existing review's name from its user account BEFORE
    #    user_id becomes optional. After this, deleting old customer
    #    accounts can't strip a review of its author's name.
    op.execute(
        "UPDATE package_reviews SET reviewer_name = "
        "(SELECT users.name FROM users WHERE users.id = package_reviews.user_id) "
        "WHERE reviewer_name IS NULL"
    )
    op.execute(
        "UPDATE testimonials SET reviewer_name = "
        "(SELECT users.name FROM users WHERE users.id = testimonials.user_id) "
        "WHERE reviewer_name IS NULL"
    )

    # 3. user_id is now optional - admin-entered reviews have no account.
    with op.batch_alter_table('package_reviews', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('testimonials', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)


def downgrade():
    # Admin-entered rows have no user, so they can't satisfy NOT NULL again.
    op.execute("DELETE FROM package_reviews WHERE user_id IS NULL")
    op.execute("DELETE FROM testimonials WHERE user_id IS NULL")

    with op.batch_alter_table('testimonials', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('reviewer_name')

    with op.batch_alter_table('package_reviews', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('image')
        batch_op.drop_column('reviewer_name')
