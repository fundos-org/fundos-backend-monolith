"""created a new UserDealPreference table and added relationship in user table and deal table

Revision ID: 61c001fbd480
Revises: 0e7cd219572c
Create Date: 2025-06-13 21:55:40.799712
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision: str = '61c001fbd480'
down_revision: Union[str, None] = '0e7cd219572c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create user_deal_preference table."""
    op.create_table(
        'userdealpreference',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('deal_id', sa.UUID(as_uuid=True), sa.ForeignKey('deal.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('not_interested', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('bookmarked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema: Drop user_deal_preference table."""
    op.drop_table('userdealpreference')
