"""added 2 columns father_name, full_name, changed the type of onboarding_status from str -> enum OnboardingStatus

Revision ID: cb85455d529d
Revises: 8658a7273756
Create Date: 2025-05-28 11:30:53.772620
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cb85455d529d'
down_revision: Union[str, None] = '8658a7273756'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add new columns
    op.add_column('user', sa.Column('full_name', sa.String(), nullable=True))
    op.add_column('user', sa.Column('father_name', sa.String(), nullable=True))

    # Set default value for onboarding_status to prevent enum conversion issues
    op.execute("""
        UPDATE "user" SET onboarding_status = 'Not_Started';
    """)

    # Create ENUM type if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboardingstatus') THEN
                CREATE TYPE onboardingstatus AS ENUM (
                    'Not_Started', 'Invitation_Code_Verified', 'Phone_Number_Verified',
                    'Email_Verified', 'Bank_Account_Verified', 'Zoho_Document_Sent',
                    'In_Progress', 'Completed', 'Pending'
                );
            END IF;
        END
        $$;
    """)

    # Alter column to use ENUM type
    op.execute("""
        ALTER TABLE "user"
        ALTER COLUMN onboarding_status
        TYPE onboardingstatus
        USING onboarding_status::text::onboardingstatus;
    """)


def downgrade() -> None:
    """Downgrade schema."""

    # Convert onboarding_status from ENUM back to VARCHAR
    op.execute("""
        ALTER TABLE "user"
        ALTER COLUMN onboarding_status
        TYPE VARCHAR
        USING onboarding_status::text;
    """)

    # Drop ENUM type
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboardingstatus') THEN
                DROP TYPE onboardingstatus;
            END IF;
        END
        $$;
    """)

    # Remove added columns
    op.drop_column('user', 'father_name')
    op.drop_column('user', 'full_name')
