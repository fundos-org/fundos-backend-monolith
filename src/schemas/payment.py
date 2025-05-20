from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional

class CreatePaymentReq(BaseModel):
    investment_id: UUID = Field(..., description="Unique identifier of the investment")
    amount: float = Field(..., gt=0, description="Payment amount")
    customer_name: str = Field(..., min_length=1, max_length=100, description="Customer's full name")
    customer_email: EmailStr = Field(..., description="Customer's email address")
    customer_phone: str = Field(..., min_length=10, max_length=15, description="Customer's phone number")
    description: Optional[str] = Field(default="Investment Payment", max_length=200, description="Payment description")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="Currency code")
    expiry_in_minutes: int = Field(default=30, ge=15, le=10080, description="Payment URL expiration time in minutes")

class CreatePaymentRes(BaseModel):
    success: bool
    data: str  # Payment URL

class WebhookResponse(BaseModel):
    success: bool
    message: str