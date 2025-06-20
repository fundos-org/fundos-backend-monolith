from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from ..models.user import Role
from datetime import datetime

class ZohoDetails(BaseModel):
    user_id: UUID = Field(...)
    name: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    father_name: Optional[str] = Field(default=None)
    entity_type: Optional[str] = Field(default=None)
    pan_number: Optional[str] = Field(default=None)
    capital_commitment: Optional[float] = Field(default=None)
    resident: Optional[str] = Field(default=None)
    date_of_birth: Optional[datetime] = Field(default=None)

    