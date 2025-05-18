from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from src.models.investment import Investment

class DealStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold"

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

class RoundType(str, Enum):
    IDEAL = "ideal"
    PRE_SEED = "pre-seed"
    SEED = "seed"
    SERIES_A = "series-a"
    SERIES_B = "series-b"
    SERIES_C = "series-c"

class Deal(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fund_manager_id: UUID = Field(foreign_key="subadmin.id")
    title: str = Field(default=None, nullable=True)
    description: str = Field(default=None, nullable=True)
    company_name: Optional[str] = Field(default=None, nullable=True)
    about_company: Optional[str] = Field(default=None, nullable=True)
    company_website: Optional[str] = Field(default=None, nullable=True)
    industry: Optional[str] = Field(default=None, nullable=True)
    problem_statement: Optional[str] = Field(default=None, nullable=True)
    business_model: Optional[BusinessModel] = Field(default=None, nullable=True)
    company_stage: Optional[CompanyStage] = Field(default=None, nullable=True)
    target_customer_segment: Optional[TargetCustomerSegment] = Field(default=None, nullable=True)
    current_valuation: Optional[float] = Field(default=None, nullable=True)
    round_size: Optional[float] = Field(default=None, nullable=True)
    syndicate_commitment: Optional[float] = Field(default=None, nullable=True)
    conversion_terms: Optional[str] = Field(default=None, nullable=True)
    instrument_type: Optional[InstrumentType] = Field(default=None, nullable=True)
    agreed_to_terms: bool = Field(default=False, nullable=True)
    logo_url: Optional[str] = Field(default=None, nullable=True)
    pitch_deck_url: Optional[str] = Field(default=None, nullable=True)
    pitch_video_url: Optional[str] = Field(default=None, nullable=True)
    status: DealStatus = Field(default=DealStatus.OPEN)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    
    # Relationships
    fund_manager: Optional["Subadmin"] = Relationship(back_populates="deals") # type: ignore # noqa: F821
    investments: List["Investment"] = Relationship(back_populates="deal") # type: ignore # noqa: F821
    investors: List["User"] = Relationship( # type: ignore # noqa: F821
        back_populates="deals",
        link_model=Investment,
        sa_relationship_kwargs={
            "secondary": "investment",
            "primaryjoin": "Deal.id == Investment.deal_id",
            "secondaryjoin": "Investment.investor_id == User.id",
            "overlaps": "deal,investments,investor",
        }
    )