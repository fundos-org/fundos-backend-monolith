from src.models.deal import BusinessModel, Industry, InstrumentType,TargetCustomerSegment, CompanyStage, RoundType
from uuid import UUID
from pydantic import BaseModel

# schemas
class DealCreateRequest(BaseModel):
    fund_manager_id: UUID


class DealCreateResponse(BaseModel):
    deal_id: UUID
    message: str

class CompanyDetailsRequest(BaseModel):
    deal_id: str
    company_name: str
    about_company: str
    company_website: str

class IndustryProblemRequest(BaseModel):
    deal_id: str
    industry: Industry
    problem_statement: str
    business_model: BusinessModel

class SecuritiesRequest(BaseModel):
    deal_id: str
    instrument_type: InstrumentType
    conversion_terms: str
    is_startup: bool
    management_fee: float
    carry: float

class CustomerSegmentRequest(BaseModel):
    deal_id: str
    company_stage: CompanyStage
    target_customer_segment: TargetCustomerSegment

class ValuationRequest(BaseModel):
    deal_id: str
    current_valuation: float
    round_size: float
    syndicate_commitment: float
    minimum_investment: float

class PitchUploadRequest(BaseModel):
    deal_id: str
    pitch_deck_url: str | None = None
    pitch_video_url: str | None = None 

class DealDataResponse(BaseModel): 
    current_valuation: float 
    round_type: RoundType
    round_size: float 
    minimum_investment: float 
    valuation_type: str  # change to enum later
    instruments: str # change to enum late 
    pass 

