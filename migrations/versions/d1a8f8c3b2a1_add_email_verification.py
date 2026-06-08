"""Add email verification fields to users table and create email_verification_tokens table."""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1a8f8c3b2a1'
down_revision = 'c474d574e45a'
branch_labels = None
depends_on = None


def upgrade():
    # Add email verification fields to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0', index=True))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    
    # Create email_verification_tokens table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('token', sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='0', index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop email_verification_tokens table
    op.drop_table('email_verification_tokens')
    
    # Remove email verification fields from users table
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
