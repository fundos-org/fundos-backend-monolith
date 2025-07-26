from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException
from typing import Any, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.utils.dependencies import get_session
from src.schemas.admin import (
    CreateProfileReq, CreateCredentialsReq, CreateProfileRes, GetSubadminRes, AdminSignInReq,
    SubadminListPaginatedResponse, SubadminDetailsResponse, SubadminDetailsUpdateRequest, SubadminDetailsUpdateResponse, AdminDashboardMetadataResponse, AdminOverviewPaginatedResponse
)
from src.services.admin import AdminService

router = APIRouter() 

admin_services = AdminService()

@router.post("/signin")
async def signin_admin(
    session: Annotated[AsyncSession, Depends(get_session)], 
    data: AdminSignInReq = Depends(), 
    ) -> Any:

    result = await admin_services.admin_signin(
        session=session,
        username=data.username, 
        password=data.password
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return result

@router.post("/subadmins/create/profile")
async def create_subadmin(
    session: Annotated[AsyncSession, Depends(get_session)], 
    data: CreateProfileReq = Depends(), 
    logo: UploadFile = File(...)
    ) -> Any:

    result = await admin_services.create_subadmin_profile(
        session=session,
        name=data.name, 
        email=data.email, 
        contact=data.contact,
        about=data.about,
        logo=logo
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return result

@router.post("/subadmins/create/credentials")
async def create_credentials(
    session:Annotated[AsyncSession, Depends(get_session)], 
    data: CreateCredentialsReq,
    ) -> Any: 
    result = await admin_services.set_subadmin_credentials(
        session=session,
        subadmin_id=data.subadmin_id,
        username=data.username, 
        password=data.password,
        re_entered_password=data.re_entered_password,
        app_name=data.app_name,
        invite_code=data.invite_code    
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to set credentials")

    return result

@router.get("/subadmins/{subadmin_id}")
async def get_subadmin(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
) -> CreateProfileRes: 

    result = await admin_services.get_subadmin_details(
        session=session,
        subadmin_id=subadmin_id
        ) 
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.get("/subadmins/")
async def get_all_subadmins(
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = 1,
    per_page: int = 20
) -> GetSubadminRes: 
    result = await admin_services.get_all_subadmins(
        session=session,
        page=page,
        per_page=per_page
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result

@router.get("/subadmins/send/invitation/")
async def send_invitation(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID = Query(..., description="ID of the subadmin")
) -> Any:
    result = await admin_services.send_invitation(
        session=session,
        subadmin_id=subadmin_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to send Invitation email")

    return result

@router.get("/subadmins", response_model=SubadminListPaginatedResponse, tags=["manish+dev_changes"])
async def get_paginated_subadmins(
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = 1,
    per_page: int = 20
):
    return await admin_services.get_paginated_subadmins(session=session, page=page, per_page=per_page)

@router.get("/subadmin_details/{subadmin_id}", response_model=SubadminDetailsResponse, tags=["manish+dev_changes"])
async def get_subadmin_details_full(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID
):
    return await admin_services.get_subadmin_full_details(session=session, subadmin_id=subadmin_id)

@router.put("/subadmin_details/{subadmin_id}", response_model=SubadminDetailsUpdateResponse, tags=["manish+dev_changes"])
async def update_subadmin_details_full(
    session: Annotated[AsyncSession, Depends(get_session)],
    subadmin_id: UUID,
    update_data: SubadminDetailsUpdateRequest
):
    return await admin_services.update_subadmin_full_details(session=session, subadmin_id=subadmin_id, update_data=update_data.dict(exclude_unset=True))

@router.get("/dashboard/metadata", response_model=AdminDashboardMetadataResponse, tags=["manish+dev_changes"])
async def get_admin_dashboard_metadata(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> AdminDashboardMetadataResponse:
    """
    Get admin dashboard metadata including:
    - total_admin_onboarded: Count of total subadmins from subadmin table
    - total_users: Count of users where role is INVESTOR from user table  
    - active_deals: Count of deals that are OPEN
    - new_user_this_month: Count of users where role is INVESTOR and created within last 30 days
    """
    return await admin_services.get_admin_dashboard_metadata(session=session)

@router.get("/overview", response_model=AdminOverviewPaginatedResponse, tags=["manish+dev_changes"])
async def get_admin_overview_paginated(
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Number of items per page (1-100)")
) -> AdminOverviewPaginatedResponse:
    """
    Get paginated admin overview including:
    - admin_name: Subadmin name
    - email: Email address of the subadmin
    - invitation_code: Invite code for the subadmin
    - total_users: Total users under that subadmin where role is INVESTOR
    - active_deals: Deals with status OPEN under that subadmin
    - onboarding_date: Created date for the subadmin
    """
    return await admin_services.get_admin_overview_paginated(session=session, page=page, per_page=per_page)
