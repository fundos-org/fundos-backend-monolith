from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.utils.dependencies import get_session
from src.schemas.subadmin import (SubAdminSignInReq, SubAdminDashboardStatisticsRes, SubAdminDashboardTransactionsRes, 
                                  SubAdminDashboardActivitiesRes, SubAdminDashboardOverviewGraphRes, SubAdminDealsOverviewRes,
                                  SubAdminDealsStatisticsRes, SubAdminMembersStatisticsRes)
from src.services.subadmin import SubAdminService

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
) -> SubAdminDashboardOverviewGraphRes: 

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
) -> SubAdminDashboardActivitiesRes: 

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
    ) -> SubAdminDealsStatisticsRes: 
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
) -> SubAdminDealsOverviewRes : 

    result = await subadmin_services.get_deals_overview(
        session=session,
        subadmin_id=subadmin_id
        ) 
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.get("/members/statistics/{subadmin_id}")
async def members_statistics(
    session:Annotated[AsyncSession, Depends(get_session)], 
    subadmin_id: UUID,
    ) -> SubAdminMembersStatisticsRes: 
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