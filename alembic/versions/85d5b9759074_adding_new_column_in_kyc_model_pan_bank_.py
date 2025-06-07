"""adding new column in kyc model: pan_bank_linked

Revision ID: 85d5b9759074
Revises: 57887b0d7c6d
Create Date: 2025-06-07 13:18:29.428610
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "85d5b9759074"
down_revision: Union[str, None] = "57887b0d7c6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "kyc",
        sa.Column("pan_bank_linked", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("kyc", "pan_bank_linked")
