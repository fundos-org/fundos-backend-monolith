from typing import Optional, Annotated
from uuid import UUID
from fastapi import UploadFile, File, Form
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from src.models.deal import DealStatus, BusinessModel, CustomerSegment, InstrumentType

class DealCreateRequest(BaseModel):
    fund_manager_id: Annotated[UUID, Form()]
    title: Annotated[Optional[str], Form()]
    description: Annotated[Optional[str], Form()]
    company_name: Annotated[Optional[str], Form()] = None
    about_company: Annotated[Optional[str], Form()] = None
    company_website: Annotated[Optional[HttpUrl], Form()] = None
    industry: Annotated[Optional[str], Form()] = None
    problem_statement: Annotated[Optional[str], Form()] = None
    business_model: Annotated[Optional[BusinessModel], Form()] = None
    business_size: Annotated[Optional[str], Form()] = None
    target_customer_segment: Annotated[Optional[CustomerSegment], Form()] = None
    current_valuation: Annotated[Optional[float], Form()] = None
    round_size: Annotated[Optional[float], Form()] = None
    syndicate_commitment: Annotated[Optional[float], Form()] = None
    conversion_terms: Annotated[Optional[str], Form()] = None
    instrument_type: Annotated[Optional[InstrumentType], Form()] = None
    agreed_to_terms: Annotated[bool, Form()]

    logo: Annotated[Optional[UploadFile], File()] = None
    pitch_deck: Annotated[Optional[UploadFile], File()] = None
    pitch_video: Annotated[Optional[UploadFile], File()] = None

class DealCreateResponse(BaseModel):
    id: UUID
    title: str
    description: str
    status: DealStatus
    created_at: datetime