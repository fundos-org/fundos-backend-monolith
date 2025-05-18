from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import uuid4, UUID
from src.models.investment import Investment

class Role(str, Enum):
    INVESTOR = "investor"
    FOUNDER = "founder"
    MENTOR = "mentor"
    VENDOR = "vendor"

class KycStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class investorType(str, Enum):
    Individual = "individual"
    Entity = "entity"

class User(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    invitation_code: str = Field(index=True, foreign_key="subadmin.invite_code")
    onboarding_status: str = Field(default="Not Started")
    email: Optional[str] = Field(unique=True, index=True, default=None)
    phone_number: Optional[str] = Field(unique=True, index=True, default=None)
    hashed_password: Optional[str] = Field(default=None)
    role: Role = Field(default=Role.INVESTOR)
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    investor_type: investorType = Field(default=investorType.Individual)
    declaration_accepted: bool = Field(default=True)
    gender: Optional[str] = Field(default=None)
    date_of_birth: Optional[str] = Field(default=None)
    care_of: Optional[str] = Field(default=None)
    aadhaar_number: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    occupation: Optional[str] = Field(default=None, nullable=True)
    income_source: Optional[str] = Field(default=None, nullable=True)
    annual_income: Optional[float] = Field(default=None, nullable=True)
    capital_commitment: Optional[float] = Field(default=None, nullable=True)
    agreement_signed: bool = Field(default=True, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now().replace(tzinfo=None))
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    fund_manager_id: Optional[UUID] = Field(foreign_key="subadmin.id")
    kyc_status: KycStatus = Field(default=KycStatus.PENDING)
    profile_image_url: Optional[str] = Field(default=None)
    
    # Relationships
    investments: List["Investment"] = Relationship(back_populates="investor") # type: ignore # noqa: F821
    subadmin: Optional["Subadmin"] = Relationship(  # noqa: F821 # type: ignore
        back_populates="users", 
        sa_relationship_kwargs={"foreign_keys": "User.fund_manager_id"
        }
    )
    deals: List["Deal"] = Relationship( # type: ignore # noqa: F821
        back_populates="investors",
        link_model=Investment,
        sa_relationship_kwargs={
            "secondary": "investment",
            "primaryjoin": "User.id == Investment.investor_id",
            "secondaryjoin": "Investment.deal_id == Deal.id",
            "overlaps":"deal,investments,investor",
        }
    )