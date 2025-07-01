"""transaction and investment table changes

Revision ID: ede2213ef9e4
Revises: cb2bb589d5d8
Create Date: 2025-07-02 01:38:41.682670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ede2213ef9e4'
down_revision: Union[str, None] = 'cb2bb589d5d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum definition
investment_status_enum = postgresql.ENUM(
    'PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', 'CANCELED',
    name='investmentstatus',
    create_type=False  # we’ll create it explicitly
)


def upgrade() -> None:
    # Create the ENUM type first
    investment_status_enum.create(op.get_bind(), checkfirst=True)

    # Alter amount column: make nullable and set default to 0.0
    op.alter_column(
        'investment', 'amount',
        existing_type=sa.FLOAT(),
        nullable=True,
        server_default=sa.text("0.0")
    )

    # Add notes column
    op.add_column(
        'investment',
        sa.Column('notes', sa.String(length=512), nullable=True)
    )

    # Add status column with enum type and default
    op.add_column(
        'investment',
        sa.Column(
            'status',
            investment_status_enum,
            nullable=False,
            server_default='PENDING'
        )
    )


def downgrade() -> None:
    # Drop status column
    op.drop_column('investment', 'status')

    # Drop notes column
    op.drop_column('investment', 'notes')

    # Revert amount column to NOT NULL and remove default
    op.alter_column(
        'investment', 'amount',
        existing_type=sa.FLOAT(),
        nullable=False,
        server_default=None
    )

    # Drop the ENUM type
    investment_status_enum.drop(op.get_bind(), checkfirst=True)
