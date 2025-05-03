from pydantic import BaseModel
from typing import Optional
# from .models import Role

class InvestmentCreate(BaseModel):
    deal_id: int
    amount: float
    payment_method: str  # e.g., "credit_card", "upi", "net_banking"

class InvestmentOut(BaseModel):
    id: int
    investor_id: int
    deal_id: int
    amount: float
    payment_status: str
    signed_document_id: Optional[str]