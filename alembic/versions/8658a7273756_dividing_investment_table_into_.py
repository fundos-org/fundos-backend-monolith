from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8658a7273756'
down_revision = 'e6df51c350e4'
branch_labels = None
depends_on = None

def upgrade():
    # Enable uuid-ossp for data migration
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create transaction table
    op.create_table(
        'transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('investment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM('PAYMENT', 'REFUND', name='transactiontype'), nullable=False),
        sa.Column('order_id', sa.String(), nullable=True),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('refund_id', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('payment_mode', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'COMPLETED', 'FAILED', 'ON_HOLD', name='transactionstatus'), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('refund_amount', sa.Float(), nullable=True),
        sa.Column('refund_status', sa.String(), nullable=True),
        sa.Column('refund_details', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['investment_id'], ['investment.id'], name='fk_transaction_investment_id'),
        sa.PrimaryKeyConstraint('id')
    )

    # Drop columns from investment table
    op.drop_column('investment', 'payment_id')
    op.drop_column('investment', 'payment_status') 

    op.execute("DROP TYPE paymentstatus;")

def downgrade():
    # Recreate paymentstatus enum
    payment_status_enum = postgresql.ENUM('PENDING', 'COMPLETED', 'FAILED', 'ON_HOLD', name='paymentstatus')
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    # Add columns back to investment table
    op.add_column('investment', sa.Column('payment_id', sa.String(), nullable=True))
    op.add_column('investment', sa.Column('payment_status', payment_status_enum, nullable=True))

    # Drop transaction table
    op.drop_table('transaction')

    # Drop enums if they are not used elsewhere
    transaction_type_enum = postgresql.ENUM(name='transactiontype')
    transaction_status_enum = postgresql.ENUM(name='transactionstatus')

    transaction_type_enum.drop(op.get_bind(), checkfirst=True)
    transaction_status_enum.drop(op.get_bind(), checkfirst=True)
