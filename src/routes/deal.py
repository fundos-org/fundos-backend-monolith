from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from starlette import status
from src.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Any
from uuid import UUID
from src.services.deal import DealService
from src.schemas.deal import (
    DealCreateRequest, DealCreateResponse, 
    CompanyDetailsRequest, IndustryProblemRequest, 
    CustomerSegmentRequest, 
    ValuationRequest, SecuritiesRequest
)

router = APIRouter(tags=["subadmin"])

# service initialization
deal_service = DealService()

@router.post("/web/create/draft")
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

@router.post("/web/company-details")
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

@router.post("/web/industry-problem")
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

@router.post("/web/customer-segment")
async def update_customer_segment( 
    data: CustomerSegmentRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> DealCreateResponse:
    try:
        deal = await deal_service.update_customer_segment(
            deal_id=data.deal_id,
            company_stage=data.company_stage, 
            target_customer_segment=data.target_customer_segment,
            session=session
        )
        return DealCreateResponse(deal_id=deal.id, message="Customer segment updated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update customer segment: {str(e)}")

@router.post("/web/valuation")
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

@router.post("/web/securities")
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

@router.get("/", tags=["investor"])
async def get_deal_by_id(
    session: Annotated[AsyncSession, Depends(get_session)], 
    deal_id: str = Query(..., description="ID of the deal"),
) -> Any:
    try:
        result = await deal_service.get_deal_by_id(
            session=session,
            deal_id=deal_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-deals", tags=["investor"])
async def get_subadmin_deals(
    session: Annotated[AsyncSession, Depends(get_session)], 
    user_id: UUID = Query(..., description="ID of the user id"),
) -> Any:
    try:
        result = await deal_service.get_deals_by_user_id(
            session=session,
            user_id=user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
