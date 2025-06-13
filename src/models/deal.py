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

class Industry(str, Enum):
    AEROSPACE = "aerospace"
    AGRITECH_AGRICULTURE = "agritech_and_agriculture"
    ARTIFICIAL_INTELLIGENCE = "artificial_intelligence"
    AUTOMOTIVE = "automotive"
    CONSUMER_ELECTRONICS = "consumer_electronics"
    DEEP_TECH = "deep_tech"
    EDTECH_EDUCATION = "edtech_and_education" 
    FINTECH_FINANCIAL_SERVICES = "fintech_and_financial_services"
    FOOD_INDUSTRY_SERVICES = "food_industury_services"
    GAMING = "gaming"
    GOVERNMENT = "government"
    HEALTHTECH_MEDTECH = "heathcare_and_medtech"
    HOSPITALITY = "hospitality"
    LIFE_SCIENCES = "life_sciences"
    MANUFACTURING = "manufacturing"
    MARKETING = "marketing"
    MEDIA = "media"
    MINING = "mining"
    NON_PROFIT = "non_profit"
    OIL_AND_GAS = "oil_and_gas"
    POWER_AND_UTILITIES = "power_and_utilities"
    PROFESSIONAL_SERVICES = "professional_services"
    REAL_ESTATE_AND_CONSTRUCTION = "real_estate_and_construction"
    RETAIL = "retail"
    ROBOTICS = "robotics"
    SOFTWARE_AND_INTERNET = "software_and_internet"
    TELECOM = "telecom"
    TRANSPORTATION = "transportation"
    TRAVEL = "travel"
    WHOLESALE_AND_DISTRIBUTION = "wholesale_and_distribution"
    OTHER = "others"

class BusinessModel(str, Enum):
    PRODUCT_BASED = "product_based"
    SERVICE_BASED = "service_based"
    SUBSCRIPTION = "subscription"
    MARKETPLACE = "marketplace"
    FREEMIUM = "freemium"
    AD_BASED = "ad_based"
    LICENSING = "licensing"
    FRANCHISE = "franchise"
    AGGREGATOR = "aggregator"
    SHARING_ECONOMY = "sharing_economy"
    DATA_MONETIZATION = "data_monetization"
    SAAS = "saas"
    ON_DEMAND = "on_demand"
    DIRECT_TO_CONSUMER = "direct_to_consumer"
    PEER_TO_PEER = "peer_to_peer" 

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
    company_name: Optional[str] = Field(default=None, nullable=True)
    about_company: Optional[str] = Field(default=None, nullable=True)
    company_website: Optional[str] = Field(default=None, nullable=True)
    industry: Optional[Industry] = Field(default=None, nullable=True)
    problem_statement: Optional[str] = Field(default=None, nullable=True)
    business_model: Optional[BusinessModel] = Field(default=None, nullable=True)
    company_stage: Optional[CompanyStage] = Field(default=None, nullable=True)
    target_customer_segment: Optional[TargetCustomerSegment] = Field(default=None, nullable=True)
    current_valuation: Optional[float] = Field(default=None, nullable=True)
    round_size: Optional[float] = Field(default=None, nullable=True)
    syndicate_commitment: Optional[float] = Field(default=None, nullable=True)
    conversion_terms: Optional[str] = Field(default=None, nullable=True)
    instrument_type: Optional[InstrumentType] = Field(default=None, nullable=True)
    minimum_investment: Optional[float] = Field(default=25000, nullable=True) 
    management_fee: Optional[float] = Field(default=0, nullable=True)
    carry: Optional[float] = Field(default=0, nullable=True)
    agreed_to_terms: bool = Field(default=False, nullable=True)
    logo_url: Optional[str] = Field(default=None, nullable=True)
    pitch_deck_url: Optional[str] = Field(default=None, nullable=True)
    pitch_video_url: Optional[str] = Field(default=None, nullable=True)
    status: DealStatus = Field(default=DealStatus.ON_HOLD)
    investment_appendix_uploaded: bool = Field(default=False, nullable=True)
    investment_appendix_key: Optional[str] = Field(default=None, nullable=True)
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
    user_preferences: List["UserDealPreference"] = Relationship(back_populates="deal") # type: ignore