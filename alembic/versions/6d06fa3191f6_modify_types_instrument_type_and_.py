"""modify types  instrument type and business model

Revision ID: 6d06fa3191f6
Revises: b367df37d3b7
Create Date: 2025-05-16 13:20:19.756535
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6d06fa3191f6'
down_revision: Union[str, None] = 'b367df37d3b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Step 1: Rename old enums
    op.execute("ALTER TYPE businessmodel RENAME TO businessmodel_old;")
    op.execute("ALTER TYPE instrumenttype RENAME TO instrumenttype_old;")

    # Step 2: Create new enums
    op.execute("CREATE TYPE businessmodel AS ENUM ("
            "'SAAS', 'TRANSACTIONAL', 'MARKETPLACE', 'ENTERPRISE', "
            "'SUBSCRIPTION', 'USAGE-BASED', 'ECOMMERCE', 'ADVERTISING');")

    op.execute("CREATE TYPE instrumenttype AS ENUM ("
            "'EQUITY', 'DEBT', 'HYBRID', 'DERIVATIVE');")

    # Step 4: Alter column types using cast
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN business_model TYPE businessmodel
        USING business_model::text::businessmodel
    """)

    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN instrument_type TYPE instrumenttype
        USING instrument_type::text::instrumenttype
    """)

    # Step 5: Drop old enums
    op.execute("DROP TYPE businessmodel_old;")
    op.execute("DROP TYPE instrumenttype_old;")

def downgrade() -> None:
    # Step 1: Recreate the *original incorrect* enums
    op.execute("CREATE TYPE businessmodel_old AS ENUM ("
               "'B2B', 'B2C', 'SAAS');")

    op.execute("CREATE TYPE instrumenttype_old AS ENUM ("
               "'CONVERTIBLE_NOTE', 'SAFE', 'EQUITY');")

    # Step 2: Change back the column types
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN business_model TYPE businessmodel_old
        USING business_model::text::businessmodel_old
    """)

    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN instrument_type TYPE instrumenttype_old
        USING instrument_type::text::instrumenttype_old
    """)

    # Step 3: Drop the correct (new) enums
    op.execute("DROP TYPE businessmodel;")
    op.execute("DROP TYPE instrumenttype;")

    # Step 4: Rename the old (wrong) enums back to original names
    op.execute("ALTER TYPE businessmodel_old RENAME TO businessmodel;")
    op.execute("ALTER TYPE instrumenttype_old RENAME TO instrumenttype;")
