from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from enum import Enum 
from uuid import UUID, uuid4

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed" 
    ON_HOLD = "on_hold"

class Investment(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    investor_id: UUID = Field(foreign_key="user.id")
    deal_id: UUID = Field(foreign_key="deal.id")
    amount: float
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)  # pending, completed, failed
    payment_id: Optional[str] = Field(default=None) # Razorpay/PayU payment ID
    signed_document_url: Optional[str] = Field(default=None) # Zoho Sign signed document ID
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: Optional[datetime]
    investor: Optional["User"] = Relationship(back_populates="investments") # type: ignore  # noqa: F821
    deal: Optional["Deal"] = Relationship(back_populates="investments") # type: ignore  # noqa: F821
