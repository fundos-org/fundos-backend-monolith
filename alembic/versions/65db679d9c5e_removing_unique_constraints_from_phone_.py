"""removing unique constraints from phone_number & email

Revision ID: 65db679d9c5e
Revises: 8a86603492c5
Create Date: 2025-06-14 16:48:54.341472
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '65db679d9c5e'
down_revision: Union[str, None] = '8a86603492c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: drop unique constraints on user.email."""
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_index("ix_user_email")


def downgrade() -> None:
    """Downgrade schema: re-add unique constraints onuser.email."""
    with op.batch_alter_table("user") as batch_op:
        batch_op.create_index("ix_user_email", ["email"], unique=True)
