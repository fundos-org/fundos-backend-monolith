from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

class TransactionType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    ON_HOLD = "on_hold"

class Transaction(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    investment_id: UUID = Field(foreign_key="investment.id")
    transaction_type: TransactionType = Field(default=TransactionType.PAYMENT)
    order_id: Optional[str] = Field(default=None)  # Payaid order_id
    transaction_id: Optional[str] = Field(default=None)  # Payaid transaction_id
    refund_id: Optional[str] = Field(default=None)  # Payaid refund_id
    amount: float
    currency: str = Field(default="INR")
    description: Optional[str] = Field(default=None)
    payment_mode: Optional[str] = Field(default=None)  # e.g., UPI, CC, NB
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    response_code: Optional[int] = Field(default=None)  # Payaid response_code
    refund_amount: Optional[float] = Field(default=None)
    refund_status: Optional[str] = Field(default=None)
    refund_details: Optional[str] = Field(default=None)  # JSON string for refund_details
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime]
    investment: Optional["Investment"] = Relationship(back_populates="transactions")  # type: ignore # noqa: F821
