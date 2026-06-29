"""drop bookings table

Revision ID: f8a2c4d6e1b9
Revises: d7e1f5b3a9c4
Create Date: 2026-06-24 00:00:00.000000

The Booking model/feature was removed: there was no UI path on the live site
that ever created a booking (every customer-facing flow — Plan My Trip,
package inquiries, visa requests — creates an Inquiry instead). Dashboard
stats, the Packages admin page, and the package-delete safety check were all
reworked to use Inquiry data in the same commit that introduced this migration.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8a2c4d6e1b9'
down_revision = 'd7e1f5b3a9c4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('bookings')


def downgrade():
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=False),
        sa.Column('contact_number', sa.String(length=20), nullable=True),
        sa.Column('num_travelers', sa.Integer(), nullable=False),
        sa.Column('travel_date', sa.Date(), nullable=False),
        sa.Column('end_travel_date', sa.Date(), nullable=True),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['tour_packages.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bookings_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_bookings_package_id'), ['package_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_bookings_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_bookings_created_at'), ['created_at'], unique=False)
