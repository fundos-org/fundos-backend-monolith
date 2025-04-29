# deal/models/deal.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
from enum import Enum

class DealStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold"

class BusinessModel(str, Enum):
    B2B = "b2b"
    B2C = "b2c"
    SAAS = "saas"

class CustomerSegment(str, Enum):
    ENTERPRISE = "enterprise"
    SME = "sme"
    CONSUMER = "consumer"

class InstrumentType(str, Enum):
    CONVERTIBLE_NOTE = "convertible_note"
    SAFE = "safe"
    EQUITY = "equity"

class Deal(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fund_manager_id: int = Field(foreign_key="user.id")
    title: str
    description: str
    company_name: Optional[str]
    about_company: Optional[str]
    company_website: Optional[str]
    industry: Optional[str]
    problem_statement: Optional[str]
    business_model: Optional[BusinessModel]
    business_size: Optional[str]
    target_customer_segment: Optional[CustomerSegment]
    current_valuation: Optional[float]
    round_size: Optional[float]
    syndicate_commitment: Optional[float]
    conversion_terms: Optional[str]
    instrument_type: Optional[InstrumentType]
    agreed_to_terms: bool = False

    logo_url: Optional[str]
    pitch_deck_url: Optional[str]
    pitch_video_url: Optional[str]

    status: DealStatus = Field(default=DealStatus.OPEN)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None