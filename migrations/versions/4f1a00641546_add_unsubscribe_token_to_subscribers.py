"""add unsubscribe token to subscribers

Revision ID: 4f1a00641546
Revises: 607877ad8fa5
Create Date: 2026-09-19 14:16:11.420953

"""
import secrets

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f1a00641546'
down_revision = '607877ad8fa5'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: add the column as optional first - adding it as required
    # in one step fails on Postgres if the table already has rows,
    # since there's nothing to put in a NOT NULL column for them yet.
    with op.batch_alter_table('subscribers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('unsubscribe_token', sa.String(length=64), nullable=True))

    # Step 2: backfill a real, unique token for every subscriber who
    # signed up before this column existed.
    subscribers_table = sa.table(
        'subscribers',
        sa.column('id', sa.Integer),
        sa.column('unsubscribe_token', sa.String),
    )
    connection = op.get_bind()
    for row in connection.execute(sa.select(subscribers_table.c.id)):
        connection.execute(
            subscribers_table.update()
            .where(subscribers_table.c.id == row.id)
            .values(unsubscribe_token=secrets.token_urlsafe(32))
        )

    # Step 3: now that every row has a value, lock it down to required
    # and unique, same as the model actually declares it.
    with op.batch_alter_table('subscribers', schema=None) as batch_op:
        batch_op.alter_column('unsubscribe_token', existing_type=sa.String(length=64), nullable=False)
        batch_op.create_unique_constraint('uq_subscribers_unsubscribe_token', ['unsubscribe_token'])


def downgrade():
    with op.batch_alter_table('subscribers', schema=None) as batch_op:
        batch_op.drop_constraint('uq_subscribers_unsubscribe_token', type_='unique')
        batch_op.drop_column('unsubscribe_token')