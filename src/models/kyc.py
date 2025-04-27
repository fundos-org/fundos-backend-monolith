from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid
# from enum import Enum 
from .user import KycStatus

class KYC(SQLModel, table=True):
    id: uuid.UUID = Field(default=None, primary_key=True, default_factory=uuid.uuid4())
    user_id: int = Field(foreign_key="user.id")
    aadhaar_number: Optional[str]  # Encrypted
    pan_number: Optional[str]  # Encrypted
    bank_account_number: Optional[str]  # Encrypted
    bank_ifsc: Optional[str]
    status: KycStatus = Field(default=KycStatus.PENDING)  # pending, verified, rejected
    # verification_details: Optional[str]  # JSON string from Digitap API 
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc)) 
    updated_at: datetime = Field(default=datetime.now(timezone.utc))