"""Add refresh tokens table

Revision ID: add_refresh_tokens_table
Revises: 8fc34fade26c
Create Date: 2025-01-27 10:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_refresh_tokens_table'
down_revision = '8fc34fade26c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create refresh_tokens table
    op.create_table('refresh_tokens',
                    sa.Column('id', postgresql.UUID(
                        as_uuid=True), nullable=False),
                    sa.Column('user_id', postgresql.UUID(
                        as_uuid=True), nullable=False),
                    sa.Column('token_hash', sa.String(
                        length=255), nullable=False),
                    sa.Column('expires_at', sa.DateTime(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True,
                              server_default=sa.text('now()')),
                    sa.Column('is_revoked', sa.Boolean(),
                              nullable=True, server_default='false'),
                    sa.Column('device_info', sa.Text(), nullable=True),
                    sa.Column('ip_address', sa.String(
                        length=45), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['user_id'], ['users.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create indexes for performance
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token_hash',
                    'refresh_tokens', ['token_hash'])
    op.create_index('ix_refresh_tokens_expires_at',
                    'refresh_tokens', ['expires_at'])
    op.create_index('ix_refresh_tokens_is_revoked',
                    'refresh_tokens', ['is_revoked'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_refresh_tokens_is_revoked', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')

    # Drop table
    op.drop_table('refresh_tokens')
