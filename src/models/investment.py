from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID, uuid4

class Investment(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    investor_id: UUID = Field(foreign_key="user.id")
    deal_id: UUID = Field(foreign_key="deal.id")
    amount: float
    signed_document_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime]
    investor: Optional["User"] = Relationship(back_populates="investments")  # type: ignore # noqa: F821
    deal: Optional["Deal"] = Relationship(back_populates="investments") # type: ignore # noqa: F821
    transactions: List["Transaction"] = Relationship(back_populates="investment") # type: ignore # noqa: F821