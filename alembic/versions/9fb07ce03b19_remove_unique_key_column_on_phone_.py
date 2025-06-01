"""remove index on phone_number, add unique constraint on fund_manager_id + phone_numberAdd commentMore actions

Revision ID: 9fb07ce03b19
Revises: cb85455d529d
Create Date: 2025-06-01 11:42:44.745657
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fb07ce03b19'
down_revision: Union[str, None] = 'cb85455d529d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the index on phone_number
    op.drop_index("ix_user_phone_number", table_name="user")

    # Add unique constraint on fund_manager_id + phone_number
    op.create_unique_constraint(
        "uq_user_fund_manager_id_phone_number",
        "user",
        ["fund_manager_id", "phone_number"]
    )


def downgrade() -> None:
    # Drop the composite unique constraint
    op.drop_constraint(
        "uq_user_fund_manager_id_phone_number",
        "user",
        type_="unique"
    )

    # Recreate the index on phone_number
    op.create_index(
        "ix_user_phone_number",
        "user",
        ["phone_number"]
    )