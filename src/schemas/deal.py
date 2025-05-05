from uuid import UUID
from fastapi import UploadFile
from pydantic import BaseModel

# schemas
class DealCreateRequest(BaseModel):
    fund_manager_id: UUID


class DealCreateResponse(BaseModel):
    deal_id: UUID
    message: str

class CompanyDetailsRequest(BaseModel):
    deal_id: UUID
    logo: UploadFile
    company_name: str
    about_company: str
    company_website: str

class IndustryProblemRequest(BaseModel):
    deal_id: UUID
    industry: str
    problem_statement: str
    business_model: str

class SecuritiesRequest(BaseModel):
    deal_id: UUID
    instrument_type: str
    conversion_terms: str
    is_startup: bool

class CustomerSegmentRequest(BaseModel):
    deal_id: UUID
    target_customer_segment: str
    customer_segment_type: str

class ValuationRequest(BaseModel):
    deal_id: UUID
    current_valuation: float
    round_size: float
    syndicate_commitment: float

class PitchUploadRequest(BaseModel):
    deal_id: UUID
    pitch_deck_url: str | None = None
    pitch_video_url: str | None = None