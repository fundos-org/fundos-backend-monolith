from pydantic import BaseModel, Field
from typing import Dict, Any


class PaymentWebhookData(BaseModel):
    encData: str = Field(..., description="Encrypted data from the payment webhook") 

class PaymentRequestData(BaseModel): 
    user_id: str = Field(..., description="User ID of the Investor")
    deal_id: str =Field(..., description="ID of the deal")
    amount: float = Field(..., description="Amount of investment")
    