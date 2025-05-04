from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
# from enum import Enum 
from .user import KycStatus

class KYC(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    user_id: UUID = Field(foreign_key="user.id")
    aadhaar_number: Optional[str]  # Encrypted
    pan_number: Optional[str]  # Encrypted
    bank_account_number: Optional[str]  # Encrypted
    bank_ifsc: Optional[str]
    status: KycStatus = Field(default=KycStatus.PENDING)  # pending, verified, rejected
    # verification_details: Optional[str]  # JSON string from Digitap API 
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc)) 
    updated_at: datetime = Field(default=datetime.now(timezone.utc))