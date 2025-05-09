from alembic import op
import sqlalchemy as sa
from typing import Union, Sequence

# revision identifiers, used by Alembic.
revision: str = '36bbe2a8ee98'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type
    op.execute("""
        CREATE TYPE companystage AS ENUM (
            'IDEAL', 'PRE_SEED', 'SEED', 'SERIES_A', 'SERIES_B', 'SERIES_C'
        );
    """)

    # Add the column using the enum type
    op.add_column('deal', sa.Column('company_stage', sa.Enum('IDEAL', 'PRE_SEED', 'SEED', 'SERIES_A', 'SERIES_B', 'SERIES_C', name='companystage'), nullable=True))

    # Create the enum type
    op.execute("""
        CREATE TYPE targetcustomersegment AS ENUM (
            'B2B', 'B2C', 'B2B2C', 'ENTERPRISE'
        );
    """)

    # Alter the column to use the enum type with a USING clause
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN target_customer_segment
        TYPE targetcustomersegment
        USING target_customer_segment::text::targetcustomersegment;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Alter the column to use the original enum type with a USING clause
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN target_customer_segment
        TYPE customersegment
        USING target_customer_segment::text::customersegment;
    """)

    # Drop the column
    op.drop_column('deal', 'company_stage')

    # Drop the enum type
    op.execute("DROP TYPE targetcustomersegment;")
    op.execute("DROP TYPE companystage;")