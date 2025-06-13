from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from starlette import status
from src.services.zoho import ZohoService
from src.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Any, Dict
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
zoho_service = ZohoService()

@router.post("/web/create/draft")
async def create_deal_draft(
    data: DealCreateRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    try:
        deal = await deal_service.create_draft(
            fund_manager_id=data.fund_manager_id, 
            session=session
        )
        return {
            "deal_data": deal, 
            "message": "Deal draft created", 
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create deal draft: {str(e)}")

@router.post("/web/company-details")
async def update_company_details(
    session: Annotated[AsyncSession, Depends(get_session)],
    background_tasks: BackgroundTasks,
    data: CompanyDetailsRequest = Depends(), 
    logo: UploadFile = File(...)
) -> Any:
    try:
        deal = await deal_service.update_company_details(
            deal_id=data.deal_id,
            logo=logo,
            company_name=data.company_name,
            about_company=data.about_company,
            company_website=data.company_website,
            session=session,
            background_tasks=background_tasks
        )
        return {
            "deal_data": deal, 
            "message": "Company details updated", 
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update company details: {str(e)}")

@router.post("/web/industry-problem")
async def update_industry_problem(
    data: IndustryProblemRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    try:
        deal = await deal_service.update_industry_problem(
            deal_id=data.deal_id,
            industry=data.industry,
            problem_statement=data.problem_statement,
            business_model=data.business_model,
            session=session
        )
        return {
            "deal_data": deal, 
            "message": "Industry and problem details updated", 
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update industry and problem details: {str(e)}")

@router.post("/web/customer-segment")
async def update_customer_segment( 
    data: CustomerSegmentRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    try:
        deal = await deal_service.update_customer_segment(
            deal_id=data.deal_id,
            company_stage=data.company_stage, 
            target_customer_segment=data.target_customer_segment,
            session=session
        )
        return {
            "deal_data": deal, 
            "message": "Customer segment updated", 
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update customer segment: {str(e)}")

@router.post("/web/valuation")
async def update_valuation(
    session: Annotated[AsyncSession, Depends(get_session)], 
    background_tasks: BackgroundTasks,
    data: ValuationRequest = Depends(), 
    pitch_deck: UploadFile = File(...), 
    pitch_video: UploadFile = File(...), 
    investment_scheme_appendix: UploadFile = File(...)
) -> Any:
    try:
        deal = await deal_service.update_valuation(
            deal_id=data.deal_id,
            current_valuation=data.current_valuation,
            round_size=data.round_size,
            syndicate_commitment=data.syndicate_commitment,
            minimum_investment=data.minimum_investment,
            pitch_deck=pitch_deck, 
            pitch_video=pitch_video,
            investment_scheme_appendix=investment_scheme_appendix,
            session=session,
            background_tasks=background_tasks
        )
        return {
            "deal_data": deal, 
            "message": "Valuation details updated", 
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update valuation details: {str(e)}")

@router.post("/web/securities")
async def update_securities( 
    data: SecuritiesRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    try:
        deal = await deal_service.update_securities(
            deal_id=data.deal_id,
            instrument_type=data.instrument_type,
            conversion_terms=data.conversion_terms,
            is_startup=data.is_startup,
            management_fee=data.management_fee, 
            carry=data.carry, 
            session=session
        )
        return {
            "deal_data": deal, 
            "message": "Securities details updated", 
            "success": True
        }
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

@router.post("/interaction")
async def register_interaction(
    session: Annotated[AsyncSession, Depends(get_session)],
    deal_id: UUID = Query(..., description="ID of the deal"),
    user_id: UUID = Query(..., description="ID of the user id"),
    not_interested: bool = False, 
    bookmarked: bool = False,
) -> Any: 
    try: 
        result = await deal_service.register_interaction(
            session=session,
            deal_id=deal_id,
            user_id=user_id,
            not_interested=not_interested,
            bookmarked=bookmarked
        )  
        return result
    except HTTPException as he : 
        raise he
    except Exception as e : 
        raise HTTPException(status_code=500, detail= str(e))

@router.post("/send/drawdown-notice", tags=["investor"])
async def send_drawdown_notice(
    session: Annotated[AsyncSession, Depends(get_session)], 
    user_id: UUID = Query(..., description="ID of the user"),
    deal_id: UUID = Query(..., description="ID of the deal"),
    investment_amount: float = Query(..., description="Amount of investment"),
) -> Dict[str, Any]:
    try:
        result = await zoho_service.send_drawdown_notice(
            session=session,
            user_id=user_id,
            deal_id=deal_id, 
            investment_amount=investment_amount
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/status", tags=["investor"])
async def get_doc_status(
    request_id: str = Query(..., description="ID of the request")
) -> Any: 
    try:
        result = await zoho_service.get_document_status(
            request_id=request_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mca/status", tags=["investor"])
async def check_mca_status(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: str = Query(..., description="ID of the user"), 
) -> Any: 
    try:
        result = await zoho_service.check_document_status_by_user_id(
            user_id=user_id, 
            session=session
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mca/download", tags=["investor"])
async def download_document(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: str = Query(..., description="ID of the user")
) -> Any: 
    try:
        result = await zoho_service.download_mca_pdf(
            user_id=user_id, 
            session=session
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))