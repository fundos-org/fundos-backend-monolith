from pydantic import BaseModel, Field
from uuid import UUID


class PaymentWebhookData(BaseModel):
    encData: str = Field(..., description="Encrypted data from the payment webhook") 

class PaymentRequestData(BaseModel): 
    user_id: UUID = Field(..., description="User ID of the Investor")
    deal_id: UUID =Field(..., description="ID of the deal")
    amount: float = Field(..., description="Amount of investment")
    idempotency_key: str = Field(..., description="Unique identifier for the payment", max_length=64)
    