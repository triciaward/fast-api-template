"""Add account deletion fields

Revision ID: add_account_deletion_fields
Revises: baa1c45958ec
Create Date: 2025-01-27 10:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_account_deletion_fields"
down_revision = "baa1c45958ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add account deletion fields to users table
    op.add_column(
        "users", sa.Column("deletion_requested_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "users", sa.Column("deletion_confirmed_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "users", sa.Column("deletion_scheduled_for", sa.DateTime(), nullable=True)
    )
    op.add_column("users", sa.Column("deletion_token", sa.String(), nullable=True))
    op.add_column(
        "users", sa.Column("deletion_token_expires", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "users", sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False)
    )


def downgrade() -> None:
    # Remove account deletion fields from users table
    op.drop_column("users", "is_deleted")
    op.drop_column("users", "deletion_token_expires")
    op.drop_column("users", "deletion_token")
    op.drop_column("users", "deletion_scheduled_for")
    op.drop_column("users", "deletion_confirmed_at")
    op.drop_column("users", "deletion_requested_at")
