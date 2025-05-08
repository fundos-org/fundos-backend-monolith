# deal/models/deal.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class DealStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold"

# Enums
class BusinessModel(str, Enum):
    SAAS = "saas"
    TRANSACTIONAL = "transactional"
    MARKETPLACE = "marketplace"
    ENTERPRISE = "enterprise"
    SUBSCRIPTION = "subscription" 
    USAGE_BASED = "usage-based"
    E_COMMERCE = "ecommerce" 
    ADVERTISING = "advertising"  

class CompanyStage(str, Enum):
    IDEAL = "ideal"
    PRE_SEED = "pre-seed"
    SEED = "seed"
    SERIES_A = "series-a" 
    SERIES_B = "series-b"
    SERIES_C = "series-c"
 
class TargetCustomerSegment(str, Enum):
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    ENTERPRISE = "enterprise" 

class InstrumentType(str, Enum):
    EQUITY = "equity"
    DEBT = "debt"
    HYBRID = "hybrid"
    DERIVATIVE = "derivative"

class Deal(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fund_manager_id: UUID = Field(foreign_key="user.id")
    title: str 
    description: str
    company_name: Optional[str]
    about_company: Optional[str]
    company_website: Optional[str]
    industry: Optional[str]
    problem_statement: Optional[str]
    business_model: Optional[BusinessModel]
    business_size: Optional[str]
    company_stage: Optional[CompanyStage]
    target_customer_segment: Optional[TargetCustomerSegment]
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
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = None