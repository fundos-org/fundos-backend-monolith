"""changing Industry and BusinessModel enum types to capital values

Revision ID: 8a86603492c5
Revises: 61c001fbd480
Create Date: 2025-06-13 23:59:48.026731
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8a86603492c5'
down_revision: Union[str, None] = '61c001fbd480'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # --- BusinessModel ---
    op.execute("ALTER TYPE businessmodel RENAME TO businessmodel_old;")
    op.execute("""
        CREATE TYPE businessmodel AS ENUM (
            'PRODUCT_BASED', 'SERVICE_BASED', 'SUBSCRIPTION', 'MARKETPLACE',
            'FREEMIUM', 'AD_BASED', 'LICENSING', 'FRANCHISE', 'AGGREGATOR',
            'SHARING_ECONOMY', 'DATA_MONETIZATION', 'SAAS',
            'ON_DEMAND', 'DIRECT_TO_CONSUMER', 'PEER_TO_PEER'
        );
    """)
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN business_model TYPE businessmodel
        USING business_model::text::businessmodel;
    """)
    op.execute("DROP TYPE businessmodel_old;")

    # --- Industry ---
    op.execute("ALTER TYPE industry RENAME TO industry_old;")
    op.execute("""
        CREATE TYPE industry AS ENUM (
            'AEROSPACE', 'AGRITECH_AND_AGRICULTURE', 'ARTIFICIAL_INTELLIGENCE',
            'AUTOMOTIVE', 'CONSUMER_ELECTRONICS', 'DEEP_TECH', 'EDTECH_AND_EDUCATION',
            'FINTECH_AND_FINANCIAL_SERVICES', 'FOOD_INDUSTRY_SERVICES', 'GAMING',
            'GOVERNMENT', 'HEALTHTECH_AND_MEDTECH', 'HOSPITALITY', 'LIFE_SCIENCES',
            'MANUFACTURING', 'MARKETING', 'MEDIA', 'MINING', 'NON_PROFIT', 'OIL_AND_GAS',
            'POWER_AND_UTILITIES', 'PROFESSIONAL_SERVICES', 'REAL_ESTATE_AND_CONSTRUCTION',
            'RETAIL', 'ROBOTICS', 'SOFTWARE_AND_INTERNET', 'TELECOM', 'TRANSPORTATION',
            'TRAVEL', 'WHOLESALE_AND_DISTRIBUTION', 'OTHER'
        );
    """)
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN industry
        TYPE industry
        USING industry::text::industry;
    """)


def downgrade() -> None:
    # --- BusinessModel (Revert) ---
    op.execute("ALTER TYPE businessmodel RENAME TO businessmodel_capital;")
    op.execute("""
        CREATE TYPE businessmodel AS ENUM (
            'product_based', 'service_based', 'subscription', 'marketplace',
            'freemium', 'ad_based', 'licensing', 'franchise', 'aggregator',
            'sharing_economy', 'data_monetization', 'saas',
            'on_demand', 'direct_to_consumer', 'peer_to_peer'
        );
    """)
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN business_model TYPE businessmodel
        USING business_model::text::businessmodel;
    """)
    op.execute("DROP TYPE businessmodel_capital;")

    # --- Industry (Revert) ---
    op.execute("ALTER TYPE industry RENAME TO industry_capital;")
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
    op.execute("""
        ALTER TABLE deal
        ALTER COLUMN industry TYPE industry
        USING industry::text::industry;
    """)
    op.execute("DROP TYPE industry_capital;")
