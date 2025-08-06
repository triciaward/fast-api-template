"""add_api_keys_table

Revision ID: 9c59b541fb4d
Revises: d5efb0f5bf2f
Create Date: 2025-07-21 14:18:05.509118

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "9c59b541fb4d"
down_revision = "d5efb0f5bf2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("scopes", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deletion_reason", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(op.f("ix_api_keys_id"), "api_keys", ["id"], unique=False)
    op.create_index(op.f("ix_api_keys_user_id"), "api_keys", ["user_id"], unique=False)
    op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)
    op.create_index(
        op.f("ix_api_keys_is_active"), "api_keys", ["is_active"], unique=False,
    )
    op.create_index(
        op.f("ix_api_keys_expires_at"), "api_keys", ["expires_at"], unique=False,
    )
    op.create_index(
        op.f("ix_api_keys_is_deleted"), "api_keys", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_api_keys_deleted_at"), "api_keys", ["deleted_at"], unique=False,
    )
    op.create_index(
        op.f("ix_api_keys_deleted_by"), "api_keys", ["deleted_by"], unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_api_keys_deleted_by"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_deleted_at"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_is_deleted"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_expires_at"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_is_active"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_key_hash"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_user_id"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_id"), table_name="api_keys")

    # Drop table
    op.drop_table("api_keys")
