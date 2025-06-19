"""add investment_scheme_appendix column to deal

Revision ID: cb2bb589d5d8
Revises: 65db679d9c5e
Create Date: 2025-06-18 01:07:04.876759
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb2bb589d5d8'
down_revision: Union[str, None] = '65db679d9c5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('deal', sa.Column('investment_scheme_appendix', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('deal', 'investment_scheme_appendix')
