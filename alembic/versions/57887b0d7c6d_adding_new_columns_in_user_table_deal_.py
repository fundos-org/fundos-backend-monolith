from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "57887b0d7c6d"
down_revision: Union[str, None] = "07b3e35457b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- user table ---------------------------------------------------------
    op.add_column(
        "user",
        sa.Column("country", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("state", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("drawdown_amount", sa.Numeric(precision=18, scale=2), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("mca_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("zoho_request_id", sa.String(length=255), nullable=True),
    )

    # --- deal table ---------------------------------------------------------
    op.add_column(
        "deal",
        sa.Column("investment_appendix_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "deal",
        sa.Column(
            "investment_appendix_uploaded",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse order of creation to avoid dependency issues
    op.drop_column("deal", "investment_appendix_uploaded")
    op.drop_column("deal", "investment_appendix_key")

    op.drop_column("user", "zoho_request_id")
    op.drop_column("user", "mca_key")
    op.drop_column("user", "drawdown_amount")
    op.drop_column("user", "state")
    op.drop_column("user", "country")
