"""transaction table: add idempotency key and payment_url

Revision ID: f1c5b8cde4bc
Revises: c008face9940
Create Date: 2025-07-02 03:11:48.614649

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1c5b8cde4bc'
down_revision: Union[str, None] = 'c008face9940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transaction', sa.Column('idempotency_key', sa.String(length=64), nullable=True))
    op.create_unique_constraint('uq_transaction_idempotency_key', 'transaction', ['idempotency_key'])

    op.add_column('transaction', sa.Column('payment_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transaction', 'payment_url')
    op.drop_constraint('uq_transaction_idempotency_key', 'transaction', type_='unique')
    op.drop_column('transaction', 'idempotency_key')
