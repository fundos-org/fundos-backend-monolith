from pydantic import BaseModel, EmailStr
from typing import Optional
from ..models.user import Role
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    role: Role = Role.INVESTOR

class UserCreate(UserBase):
    password: str
    unique_id: str

class UserOut(UserBase):
    id: int
    unique_id: str
    kyc_status: str
    created_at: datetime

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str

    