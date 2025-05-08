from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from starlette import status
from src.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.services.deal import DealService
from src.schemas.deal import (
    DealCreateRequest, DealCreateResponse, CompanyDetailsRequest, IndustryProblemRequest, CustomerSegmentRequest, 
    ValuationRequest, SecuritiesRequest
)

router = APIRouter()

# service initialization
deal_service = DealService()

@router.post("/create/draft")
async def create_deal_draft(
    data: DealCreateRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> DealCreateResponse:
    try:
        deal = await deal_service.create_draft(
            fund_manager_id=data.fund_manager_id, 
            session=session
        )
        return DealCreateResponse(deal_id=deal.id, message="Deal draft created")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create deal draft: {str(e)}")

@router.patch("/deal/company-details")
async def update_company_details(
    session: Annotated[AsyncSession, Depends(get_session)],
    data: CompanyDetailsRequest = Depends(), 
    logo: UploadFile = File(...)
) -> DealCreateResponse:
    try:
        deal = await deal_service.update_company_details(
            deal_id=data.deal_id,
            logo= logo,
            company_name=data.company_name,
            about_company=data.about_company,
            company_website=data.company_website,
            session=session
        )
        return DealCreateResponse(deal_id=deal.id, message="Company details updated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update company details: {str(e)}")

@router.patch("/deal/industry-problem")
async def update_industry_problem(
    data: IndustryProblemRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> DealCreateResponse:
    try:
        deal = await deal_service.update_industry_problem(
            deal_id=data.deal_id,
            industry=data.industry,
            problem_statement=data.problem_statement,
            business_model=data.business_model,
            session=session
        )
        return DealCreateResponse(deal_id=deal.id, message="Industry and problem details updated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update industry and problem details: {str(e)}")

@router.patch("/deal/customer-segment")
async def update_customer_segment( 
    data: CustomerSegmentRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> DealCreateResponse:
    try:
        deal = await deal_service.update_customer_segment(
            deal_id=data.deal_id,
            target_customer_segment=data.target_customer_segment,
            customer_segment_type=data.customer_segment_type,
            session=session
        )
        return DealCreateResponse(deal_id=deal.id, message="Customer segment updated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update customer segment: {str(e)}")

@router.patch("/deal/valuation")
async def update_valuation(
    session: Annotated[AsyncSession, Depends(get_session)], 
    data: ValuationRequest = Depends(), 
    pitch_deck: UploadFile = File(...), 
    pitch_video: UploadFile = File(...)
) -> DealCreateResponse:
    try:
        deal = await deal_service.update_valuation(
            deal_id=data.deal_id,
            current_valuation=data.current_valuation,
            round_size=data.round_size,
            syndicate_commitment=data.syndicate_commitment,
            pitch_deck=pitch_deck, 
            pitch_video=pitch_video,
            session=session
        )
        return DealCreateResponse(deal_id=deal.id, message="Valuation details updated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update valuation details: {str(e)}")

@router.patch("/deal/securities")
async def update_securities( 
    data: SecuritiesRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> DealCreateResponse:
    try:
        deal = await deal_service.update_securities(
            deal_id=data.deal_id,
            instrument_type=data.instrument_type,
            conversion_terms=data.conversion_terms,
            is_startup=data.is_startup,
            session=session
        )
        return DealCreateResponse(deal_id=deal.id, message="Securities details updated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update securities details: {str(e)}")
