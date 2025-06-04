from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Any, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.utils.dependencies import get_session
from src.schemas.admin import (CreateProfileReq, CreateCredentialsReq, CreateProfileRes, GetSubadminRes, AdminSignInReq)
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
    session: Annotated[AsyncSession, Depends(get_session)]
) -> GetSubadminRes: 
    result = await admin_services.get_all_subadmins(
        session=session
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result



