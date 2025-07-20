"""merge account deletion and password reset migrations

Revision ID: 8fc34fade26c
Revises: add_account_deletion_fields, add_password_reset_fields
Create Date: 2025-07-20 10:05:36.158374

"""


# revision identifiers, used by Alembic.
revision = "8fc34fade26c"
down_revision = ("add_account_deletion_fields", "add_password_reset_fields")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
