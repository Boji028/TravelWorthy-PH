"""add offer details, gallery and dates

Adds flier, duration, location, highlights, inclusions and exclusions to
offers, plus offer_images (gallery) and offer_dates (available dates).

Revision ID: f7b2d4e81a36
Revises: e5a1c7d93f20
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa


revision = 'f7b2d4e81a36'
down_revision = 'e5a1c7d93f20'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('flier_image', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('duration', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('highlights', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('inclusions', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('exclusions', sa.Text(), nullable=True))

    op.create_table(
        'offer_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.Integer(), sa.ForeignKey('offers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('path', sa.String(length=300), nullable=False),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_offer_images_offer_id', 'offer_images', ['offer_id'])

    op.create_table(
        'offer_dates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.Integer(), sa.ForeignKey('offers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('note', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_offer_dates_offer_id', 'offer_dates', ['offer_id'])


def downgrade():
    op.drop_index('ix_offer_dates_offer_id', table_name='offer_dates')
    op.drop_table('offer_dates')
    op.drop_index('ix_offer_images_offer_id', table_name='offer_images')
    op.drop_table('offer_images')
    with op.batch_alter_table('offers', schema=None) as batch_op:
        for col in ('exclusions', 'inclusions', 'highlights', 'location', 'duration', 'flier_image'):
            batch_op.drop_column(col)
