from src.models.deal import BusinessModel, InstrumentType,TargetCustomerSegment, CompanyStage
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
    industry: str
    problem_statement: str
    business_model: BusinessModel

class SecuritiesRequest(BaseModel):
    deal_id: str
    instrument_type: InstrumentType
    conversion_terms: str
    is_startup: bool

class CustomerSegmentRequest(BaseModel):
    deal_id: str
    company_stage: CompanyStage
    target_customer_segment: TargetCustomerSegment

class ValuationRequest(BaseModel):
    deal_id: str
    current_valuation: float
    round_size: float
    syndicate_commitment: float

class PitchUploadRequest(BaseModel):
    deal_id: str
    pitch_deck_url: str | None = None
    pitch_video_url: str | None = None