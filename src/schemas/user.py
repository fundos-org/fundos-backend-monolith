from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ZohoDetails(BaseModel):
    user_id: UUID = Field(...)
    full_name: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    father_name: Optional[str] = Field(default=None)
    investor_type: Optional[str] = Field(default=None)
    pan_number: Optional[str] = Field(default=None)
    capital_commitment: Optional[float] = Field(default=None)
    country: Optional[str] = Field(default=None)
    date_of_birth: Optional[str] = Field(default=None)

    