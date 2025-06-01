"""removed title and description columns from deals

Revision ID: 07b3e35457b4
Revises: 3060ce5c10af
Create Date: 2025-06-02 03:51:00.761019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07b3e35457b4'
down_revision: Union[str, None] = '9fb07ce03b19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - remove columns."""
    with op.batch_alter_table("deal") as batch_op:
        batch_op.drop_column("title")
        batch_op.drop_column("description")


def downgrade() -> None:
    """Downgrade schema - add columns back."""
    with op.batch_alter_table("deal") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("title", sa.String(length=255), nullable=True))
