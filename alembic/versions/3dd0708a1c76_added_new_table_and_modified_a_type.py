"""added new table and modified a type  

Revision ID: 3dd0708a1c76
Revises: 6d06fa3191f6
Create Date: 2025-05-17 13:31:53.003193
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3dd0708a1c76'
down_revision: Union[str, None] = '6d06fa3191f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# new ENUM type
new_role_enum = postgresql.ENUM(
    "INVESTOR", "FOUNDER", "MENTOR", "VENDOR",
    name="role",
    create_type=False  # avoid auto-creation here so we can handle it explicitly
)

old_enum = postgresql.ENUM(
    "INVESTOR", "FOUNDER", "MENTOR", "VENDOR", "ADMIN", "FUND_MANAGER", 
    name="role", 
    create_type=False
)


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Create new ENUM and replace old one
    # Step 1: Rename the old enum type
    op.execute("ALTER TYPE role RENAME TO role_old")

    # Step 2: Create the new enum type
    new_role_enum.create(op.get_bind())

    # Step 3: Alter column to use new enum type
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE role USING role::text::role")

    # Step 4: Drop the old enum type
    op.execute("DROP TYPE role_old")

    # 2. Create subadmin table
    op.create_table(
        "subadmin",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("contact", sa.String(), nullable=True),
        sa.Column("about", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False, unique=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("re_entered_password", sa.String(), nullable=True),
        sa.Column("app_name", sa.String(), nullable=True),
        sa.Column("invite_code", sa.String(), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


    # 3. Alter fund_manager_id foreign key
    op.drop_constraint("user_fund_manager_id_fkey", "user", type_="foreignkey")
    op.create_foreign_key(
        "user_fund_manager_id_fkey", "user", "subadmin", ["fund_manager_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""

    # 1. Revert foreign key
    op.drop_constraint("user_fund_manager_id_fkey", "user", type_="foreignkey")
    op.create_foreign_key(
        "user_fund_manager_id_fkey", "user", "user", ["fund_manager_id"], ["id"]
    )

    # 2. Drop subadmin table
    op.drop_table("subadmin")

    # 3. Revert role ENUM
        # Recreate old enum
    old_enum.create(op.get_bind())

    # Revert column type
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE role_old USING role::text::role_old")

    # Drop new enum
    op.execute("DROP TYPE role")

    # Rename old enum back
    op.execute("ALTER TYPE role_old RENAME TO role")
    # You should recreate the old ENUM if needed. For now we'll just leave the column untyped if downgrade is rare.
