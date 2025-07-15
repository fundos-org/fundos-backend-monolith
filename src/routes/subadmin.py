from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.models.deal import DealStatus
from src.utils.dependencies import get_session
from src.schemas.subadmin import (SubAdminSignInReq, SubAdminDashboardStatisticsRes, SubAdminDashboardTransactionsRes, 
                                  SubAdminDashboardActivitiesRes, SubAdminDashboardOverviewGraphRes, SubAdminDealsOverviewRes,
                                  SubAdminDealsStatisticsRes, SubAdminMembersStatisticsRes, InvestorListResponse, InvestorListMetadata,
                                  DeleteInvestorResponse, UpdateInvestorResponse, InvestorInfoResponse, InvestorInvestmentsResponse, InvestorInvestmentsMetadataResponse, InvestorTransactionsResponse,
                                  InvestorDocumentsResponse, MarkDealInactiveResponse, EditDealRequest, EditDealResponse, DealDetailsResponse, DealAboutResponse, DealInvestorsResponse, DealTransactionsResponse,
                                  DealDocumentsResponse, WelcomeMailResponse, OnboardingMailResponse, ConsentMailResponse, WelcomeMailUpdateResponse, OnboardingMailUpdateResponse, ConsentMailUpdateResponse)
from src.services.subadmin import SubAdminService
from src.models.user import User, Role
from src.models.transaction import Transaction
from sqlalchemy import select
import logging
from fastapi import status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter() 

subadmin_services = SubAdminService()

@router.post("/signin")
async def signin_subadmin(
    session: Annotated[AsyncSession, Depends(get_session)], 
    data: SubAdminSignInReq = Depends(), 
) -> Any:

    result = await subadmin_services.subadmin_signin(
        session=session,
        username=data.username, 
        password=data.password
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return result

@router.get("/dashboard/statistics/{subadmin_id}")
async def statistics(
    session:Annotated[AsyncSession, Depends(get_session)], 
    subadmin_id: UUID,
) -> SubAdminDashboardStatisticsRes: 
    result = await subadmin_services.get_dashboard_statistics(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to set credentials")

    return result

@router.get("/dashboard/overview/{subadmin_id}")
async def overview(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> Any: 

    result = await subadmin_services.get_overview_graph(
        session=session,
        subadmin_id=subadmin_id
        ) 
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.get("/dashboard/activities/{subadmin_id}")
async def activities(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> Any: 

    result = await subadmin_services.get_activities(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.get("/dashboard/transactions/{subadmin_id}")
async def transactions(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> SubAdminDashboardTransactionsRes: 

    result = await subadmin_services.get_transactions_details(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.get("/deals/statistics/{subadmin_id}")
async def deals_statistics(
    session:Annotated[AsyncSession, Depends(get_session)], 
    subadmin_id: UUID,
) -> Any: 
    result = await subadmin_services.get_deals_statistics(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get deals statistics")

    return result

@router.get("/deals/overview/{subadmin_id}")
async def deals_overview(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> Any: 

    result = await subadmin_services.get_deals_overview(
        session=session,
        subadmin_id=subadmin_id
        ) 
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.post("/deals/change/status")
async def members_overview(
    session: Annotated[AsyncSession, Depends(get_session)],
    deal_id: UUID, 
    status: DealStatus
) -> Any:
    try:
        result = await subadmin_services.change_deal_status(
            session=session,
            deal_id=deal_id, 
            deal_status=status
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/members/statistics/{subadmin_id}")
async def members_statistics(
    session:Annotated[AsyncSession, Depends(get_session)], 
    subadmin_id: UUID,
) -> Any: 
    result = await subadmin_services.get_members_statistics(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to set credentials")

    return result

@router.post("/members/addmember/{subadmin_id}/{email}")
async def add_member(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    email: str
) -> Any: 

    result = await subadmin_services.add_members(
        session=session,
        subadmin_id=subadmin_id,
        email=email
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.get("/investors/list/{subadmin_id}", tags=["manish_dev_changes"])
async def get_investors_list(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    page: int = 1,
    per_page: int = 20
) -> InvestorListResponse:
    result = await subadmin_services.get_investors_list(
        session=session,
        subadmin_id=subadmin_id,
        page=page,
        per_page=per_page
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch investors list")

    return result

@router.get("/investors/metadata/{subadmin_id}", tags=["manish_dev_changes"])
async def get_investors_metadata(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> InvestorListMetadata:
    result = await subadmin_services.get_investors_metadata(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch investors metadata")

    return result

@router.delete("/investors/delete/{subadmin_id}/{investor_id}", tags=["manish_dev_changes"])
async def delete_investor(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    investor_id: UUID
) -> DeleteInvestorResponse:
    result = await subadmin_services.delete_investor(
        session=session,
        subadmin_id=subadmin_id,
        investor_id=investor_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to delete investor")

    return result

@router.put("/investors/update/{subadmin_id}/{investor_id}", tags=["manish_dev_changes"])
async def update_investor(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    investor_id: UUID,
    update_data: dict
) -> UpdateInvestorResponse:
    result = await subadmin_services.update_investor(
        session=session,
        subadmin_id=subadmin_id,
        investor_id=investor_id,
        update_data=update_data
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to update investor")

    return result

@router.get("/investors/abount_info/{investor_id}", tags=["manish_dev_changes"])
async def get_investor_about_info(
    session: Annotated[AsyncSession, Depends(get_session)],
    investor_id: UUID
) -> InvestorInfoResponse:
    result = await subadmin_services.get_investor_about_info(
        session=session,
        investor_id=investor_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch investor info")

    return result

@router.get("/investors/investments_info/{investor_id}", tags=["manish_dev_changes"])
async def get_investor_investments_info(
    session: Annotated[AsyncSession, Depends(get_session)],
    investor_id: UUID
) -> InvestorInvestmentsResponse:
    result = await subadmin_services.get_investor_investments_info(
        session=session,
        investor_id=investor_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch investor investments info")

    return result

@router.get("/investors/investments_metadata/{investor_id}", tags=["manish_dev_changes"])
async def get_investor_investments_metadata(
    session: Annotated[AsyncSession, Depends(get_session)],
    investor_id: UUID
) -> InvestorInvestmentsMetadataResponse:
    result = await subadmin_services.get_investor_investments_metadata(
        session=session,
        investor_id=investor_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch investor investments metadata")

    return result

@router.get("/investors/transactions/{investor_id}", tags=["manish_dev_changes"])
async def get_investor_transactions(
    session: Annotated[AsyncSession, Depends(get_session)],
    investor_id: UUID
) -> InvestorTransactionsResponse:
    result = await subadmin_services.get_investor_transactions(
        session=session,
        investor_id=investor_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch investor transactions")

    return result

@router.get("/investors/documents_info/{investor_id}", tags=["manish_dev_changes"])
async def get_investor_documents_info(
    session: Annotated[AsyncSession, Depends(get_session)],
    investor_id: UUID
) -> InvestorDocumentsResponse:
    result = await subadmin_services.get_investor_documents_info(
        session=session,
        investor_id=investor_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch investor documents info")

    return result

@router.post("/deals/mark_inactive/{subadmin_id}/{deal_id}", tags=["manish_dev_changes"])
async def mark_deal_inactive(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    deal_id: UUID
) -> MarkDealInactiveResponse:
    result = await subadmin_services.mark_deal_inactive(
        session=session,
        subadmin_id=subadmin_id,
        deal_id=deal_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to mark deal inactive")

    return result

@router.get("/deals/deal_details/{subadmin_id}/{deal_id}", tags=["manish_dev_changes"])
async def get_deal_details(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    deal_id: UUID
) -> DealDetailsResponse:
    result = await subadmin_services.get_deal_details(
        session=session,
        subadmin_id=subadmin_id,
        deal_id=deal_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch deal details")

    return result

@router.put("/deals/edit_deals/{subadmin_id}/{deal_id}", tags=["manish_dev_changes"])
async def edit_deal(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    deal_id: UUID,
    update_data: EditDealRequest
) -> EditDealResponse:
    result = await subadmin_services.edit_deal(
        session=session,
        subadmin_id=subadmin_id,
        deal_id=deal_id,
        update_data=update_data.dict(exclude_unset=True)
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to update deal details")

    return result

@router.get("/deals/deal_info/about/{subadmin_id}/{deal_id}", tags=["manish_dev_changes"])
async def get_deal_about_info(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    deal_id: UUID
) -> DealAboutResponse:
    result = await subadmin_services.get_deal_about_info(
        session=session,
        subadmin_id=subadmin_id,
        deal_id=deal_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch deal about info")

    return result

@router.get("/deals/deal_info/investors/{deal_id}", tags=["manish_dev_changes"])
async def get_deal_investors(
    session: Annotated[AsyncSession, Depends(get_session)],
    deal_id: UUID,
    page: int = 1,
    per_page: int = 20
) -> DealInvestorsResponse:
    result = await subadmin_services.get_deal_investors(
        session=session,
        deal_id=deal_id,
        page=page,
        per_page=per_page
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch deal investors")

    return result

@router.get("/deals/deal_info/transactions/{deal_id}", tags=["manish_dev_changes"])
async def get_deal_transactions(
    session: Annotated[AsyncSession, Depends(get_session)],
    deal_id: UUID,
    page: int = 1,
    per_page: int = 20
) -> DealTransactionsResponse:
    result = await subadmin_services.get_deal_transactions(
        session=session,
        deal_id=deal_id,
        page=page,
        per_page=per_page
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch deal transactions")

    return result

@router.get("/deals/deal_info/documents/{deal_id}", tags=["manish_dev_changes"])
async def get_deal_documents(
    session: Annotated[AsyncSession, Depends(get_session)],
    deal_id: UUID
) -> DealDocumentsResponse:
    result = await subadmin_services.get_deal_documents(
        session=session,
        deal_id=deal_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch deal documents")

    return result

@router.get("/communication/welcome_mail_get/{subadmin_id}", tags=["manish_dev_changes"])
async def get_welcome_mail(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> WelcomeMailResponse:
    result = await subadmin_services.get_welcome_mail(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch welcome mail")

    return result

@router.put("/communication/welcome_mail_update/{subadmin_id}", tags=["manish_dev_changes"])
async def update_welcome_mail(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    update_data: dict
) -> WelcomeMailUpdateResponse:
    result = await subadmin_services.update_welcome_mail(
        session=session,
        subadmin_id=subadmin_id,
        update_data=update_data
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to update welcome mail")

    return result

@router.get("/communication/onboarding_mail_get/{subadmin_id}", tags=["manish_dev_changes"])
async def get_onboarding_mail(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> OnboardingMailResponse:
    result = await subadmin_services.get_onboarding_mail(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch onboarding mail")

    return result

@router.put("/communication/onboarding_mail_update/{subadmin_id}", tags=["manish_dev_changes"])
async def update_onboarding_mail(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    update_data: dict
) -> OnboardingMailUpdateResponse:
    result = await subadmin_services.update_onboarding_mail(
        session=session,
        subadmin_id=subadmin_id,
        update_data=update_data
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to update onboarding mail")

    return result

@router.get("/communication/consent_mail_get/{subadmin_id}", tags=["manish_dev_changes"])
async def get_consent_mail(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> ConsentMailResponse:
    result = await subadmin_services.get_consent_mail(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to fetch consent mail")

    return result

@router.put("/communication/consent_mail_update/{subadmin_id}", tags=["manish_dev_changes"])
async def update_consent_mail(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    update_data: dict
) -> ConsentMailUpdateResponse:
    result = await subadmin_services.update_consent_mail(
        session=session,
        subadmin_id=subadmin_id,
        update_data=update_data
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to update consent mail")

    return result