from pydantic import BaseModel
from typing import Optional
import datetime
# from .models import Role

class DealCreate(BaseModel):
    title: str
    description: str
    amount: float
    legal_document_id: Optional[str]

class DealOut(BaseModel):
    id: int
    fund_manager_id: int
    title: str
    description: str
    amount: float
    status: str
    created_at: datetime