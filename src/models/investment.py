from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4

class InvestmentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELED = "CANCELED"

class Investment(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    investor_id: UUID = Field(foreign_key="user.id")
    deal_id: UUID = Field(foreign_key="deal.id")
    amount: Optional[float] = Field(default=0.0)
    status: InvestmentStatus = Field(default=InvestmentStatus.PENDING)
    signed_document_url: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=512)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime]
    investor: Optional["User"] = Relationship(back_populates="investments")  # type: ignore # noqa: F821
    deal: Optional["Deal"] = Relationship(back_populates="investments") # type: ignore # noqa: F821
    transactions: List["Transaction"] = Relationship(back_populates="investment") # type: ignore # noqa: F821