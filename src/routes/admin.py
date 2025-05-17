from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Any, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.dependencies import get_session
from src.schemas.admin import (CreateProfileReq, CreateCredentialsReq, CreateProfileRes)
from src.services.admin import SubAdminService

router = APIRouter() 

subadmin_services = SubAdminService()

@router.post("/create/profile")
async def create_subadmin(
    session: Annotated[AsyncSession, Depends(get_session)], 
    data: CreateProfileReq = Depends(), 
    logo: UploadFile = File(...)
    ) -> Any:

    result = await subadmin_services.create_subadmin_profile(
        session=session,
        name=data.name, 
        email=data.email, 
        contact=data.contact,
        logo=logo
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return result

@router.post("/create/credentials")
async def create_credentials(
    session:Annotated[AsyncSession, Depends(get_session)], 
    data: CreateCredentialsReq = Depends(),
    ) -> Any: 
    result = await subadmin_services.set_subadmin_credentials(
        session=session,
        username=data.username, 
        password=data.password,
        re_entered_password=data.re_entered_password,
        app_name=data.app_name,
        invite_code=data.invite_code    
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to set credentials")

    return result

@router.get("/create/")
async def get_subadmin(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> CreateProfileRes: 

    result = await subadmin_services.get_subadmin_details(session=session) 
    if not result["success"]:
        raise HTTPException(status_code=400, detail="failed to get subadmin details")

    return result





