from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

class UserDealPreference(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    deal_id: UUID = Field(foreign_key="deal.id", index=True)
    not_interested: bool = Field(default=False)
    bookmarked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships
    user: "User" = Relationship(back_populates="deal_preferences") # type: ignore
    deal: "Deal" = Relationship(back_populates="user_preferences") # type: ignore