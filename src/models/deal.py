from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum 
import uuid
from .investment import Investment

class DealStatus(str, Enum): 
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold" 

class Deal(SQLModel, table=True):
    id: uuid.UUID = Field(default=None, primary_key=True, default_factory=uuid.uuid4())
    fund_manager_id: int = Field(foreign_key="user.id")
    title: str
    description: str
    amount: float
    status: DealStatus = Field(default=DealStatus.OPEN)  # open, closed, funded
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: Optional[datetime]
    # fund_manager: Optional[User] = Relationship(back_populates="deals")
    investment_ids: List[int] = Field(foreign_key= Investment.id) # current it is int -> change it to uuid later. think about relationship back propogation. 
    legal_document_url: Optional[str]  # Zoho Sign document s3 object url 
