"""added columns in deal min investment, management fee, carry, changed types for industry, updated business model type

Revision ID: 0e7cd219572c
Revises: 85d5b9759074
Create Date: 2025-06-13 21:22:46.786261
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0e7cd219572c'
down_revision: Union[str, None] = '85d5b9759074'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Step 1: Add new columns
    op.add_column('deal', sa.Column('minimum_investment', sa.Numeric(), nullable=True))
    op.add_column('deal', sa.Column('management_fee', sa.Numeric(), nullable=True))
    op.add_column('deal', sa.Column('carry', sa.Numeric(), nullable=True))

    # Step 2: Rename old enums
    op.execute("ALTER TYPE businessmodel RENAME TO businessmodel_old;")

    # Step 3: Create new businessmodel enum (based on model)
    op.execute("""
        CREATE TYPE businessmodel AS ENUM (
            'product_based', 'service_based', 'subscription', 'marketplace',
            'freemium', 'ad_based', 'licensing', 'franchise', 'aggregator',
            'sharing_economy', 'data_monetization', 'saas',
            'on_demand', 'direct_to_consumer', 'peer_to_peer'
        );
    """)

    # Step 4: Alter column to use new enum
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN business_model TYPE businessmodel
        USING business_model::text::businessmodel;
    """)

    # Step 5: Drop old enum
    op.execute("DROP TYPE businessmodel_old;")

    # Step 6: Create and apply new industry enum (assuming similar revamp)
    op.execute("""
        CREATE TYPE industry AS ENUM (
            'aerospace', 'agritech_and_agriculture', 'artificial_intelligence',
            'automotive', 'consumer_electronics', 'deep_tech', 'edtech_and_education',
            'fintech_and_financial_services', 'food_industury_services', 'gaming',
            'government', 'heathcare_and_medtech', 'hospitality', 'life_sciences',
            'manufacturing', 'marketing', 'media', 'mining', 'non_profit', 'oil_and_gas',
            'power_and_utilities', 'professional_services', 'real_estate_and_construction',
            'retail', 'robotics', 'software_and_internet', 'telecom', 'transportation',
            'travel', 'wholesale_and_distribution', 'others'
        );
    """)

    # Step 7: use the new type created for industry
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN industry
        TYPE industry
        USING industry::industry;
    """)


def downgrade() -> None:
    # Drop new columns
    op.drop_column('deal', 'carry')
    op.drop_column('deal', 'management_fee')
    op.drop_column('deal', 'minimum_investment')

    # Recreate old businessmodel enum
    op.execute("""
            CREATE TYPE businessmodel AS ENUM (
            'SAAS', 'TRANSACTIONAL', 'MARKETPLACE', 'ENTERPRISE',
            'SUBSCRIPTION', 'USAGE-BASED', 'ECOMMERCE', 'ADVERTISING'
        );
    """)

    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN business_model TYPE businessmodel_old
        USING business_model::text::businessmodel_old;
    """)
    op.execute("DROP TYPE businessmodel;")
    op.execute("ALTER TYPE businessmodel_old RENAME TO businessmodel;")

    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN industry 
        TYPE TEXT
        USING industry::text;
    """)
    op.execute("DROP TYPE industry;")
