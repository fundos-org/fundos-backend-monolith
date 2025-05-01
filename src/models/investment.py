from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum 
import uuid

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed" 
    ON_HOLD = "on_hold"

class Investment(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4())
    investor_id: int = Field(foreign_key="user.id")
    deal_id: int = Field(foreign_key="deal.id")
    amount: float
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)  # pending, completed, failed
    payment_id: Optional[str]  # Razorpay/PayU payment ID
    signed_document_url: Optional[str]  # Zoho Sign signed document ID
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: Optional[datetime]
    # investor: Optional[User] = Relationship(back_populates="investments")
    # deal: Optional[Deal] = Relationship(back_populates="investments")