"""transaction table: add user_id and deal_id

Revision ID: c008face9940
Revises: ede2213ef9e4
Create Date: 2025-07-02 01:56:23.662933
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c008face9940'
down_revision: Union[str, None] = 'ede2213ef9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transaction', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('transaction', sa.Column('deal_id', sa.UUID(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transaction', 'deal_id')
    op.drop_column('transaction', 'user_id')
